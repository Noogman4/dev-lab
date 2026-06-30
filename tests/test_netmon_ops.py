import threading

from tools.netmon_ops import NetworkOperationCoordinator, RollbackTransaction


def test_network_operation_coordinator_blocks_parallel_and_logs_busy_message():
    logs = []
    coordinator = NetworkOperationCoordinator(log_busy_fn=logs.append)

    assert coordinator.try_begin("Internet AN") is True

    other_done = []

    def worker():
        other_done.append(
            coordinator.try_begin("VPN wechseln auf proton", log_busy=True)
        )

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    assert other_done == [False]
    assert logs == [
        "Netzwerkaktion blockiert: VPN wechseln auf proton wird nicht gestartet, da bereits 'Internet AN' läuft."
    ]

    coordinator.end()


def test_network_operation_coordinator_reentrant_depth_and_release():
    coordinator = NetworkOperationCoordinator()

    assert coordinator.try_begin("Killswitch aktivieren") is True
    assert coordinator.try_begin("Killswitch aktivieren") is True
    assert coordinator.depth == 2

    coordinator.end()
    assert coordinator.depth == 1
    assert coordinator.active_operation == "Killswitch aktivieren"

    coordinator.end()
    assert coordinator.depth == 0
    assert coordinator.active_operation == ""
    assert coordinator.owner_thread_id is None


def test_rollback_transaction_runs_callbacks_in_reverse_order():
    called = []
    tx = RollbackTransaction("Test")

    tx.add_rollback("first", lambda: called.append("first"))
    tx.add_rollback("second", lambda: called.append("second"))

    assert tx.rollback() is True
    assert called == ["second", "first"]


def test_rollback_transaction_reports_failure_and_continues_callbacks():
    called = []
    logs = []
    debugs = []

    def boom():
        raise RuntimeError("x")

    tx = RollbackTransaction("Test", log_fn=logs.append, log_debug_fn=debugs.append)
    tx.add_rollback("bad", boom)
    tx.add_rollback("good", lambda: called.append("good"))

    assert tx.rollback() is False
    assert called == ["good"]
    assert logs
    assert "Rollback fehlgeschlagen" in logs[0]
    assert debugs


def test_rollback_transaction_commit_skips_rollback_callbacks():
    called = []
    tx = RollbackTransaction("Test")
    tx.add_rollback("first", lambda: called.append("first"))

    tx.commit()

    assert tx.rollback() is True
    assert called == []
