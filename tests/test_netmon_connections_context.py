import inspect

import netmon.app as app_module
from netmon.app import App


class DummyConnTable:
    def __init__(self, items, selected=None):
        self.items = items
        self.selected_items = tuple(selected or ())

    def selection(self):
        return self.selected_items

    def get_children(self):
        return tuple(self.items.keys())

    def item(self, item_id, option):
        if option == "values":
            return self.items[item_id]
        raise KeyError(option)


class DummyArpTable:
    def __init__(self):
        self.rows = {}
        self.order = []
        self.counter = 0

    def get_children(self):
        return tuple(self.order)

    def delete(self, item_id):
        self.order.remove(item_id)
        self.rows.pop(item_id, None)

    def insert(self, _parent, _index, values):
        self.counter += 1
        item_id = f"row{self.counter}"
        self.order.append(item_id)
        self.rows[item_id] = tuple(values)
        return item_id


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


def test_get_connections_analysis_text_prefers_selected_rows():
    app = App.__new__(App)
    app.conn_table = DummyConnTable(
        {
            "row1": ("tcp", "ESTAB", "127.0.0.1:22", "1.2.3.4:5555", "123", "sshd"),
            "row2": ("udp", "UNCONN", "0.0.0.0:53", "0.0.0.0:*", "-", "systemd"),
        },
        selected=["row1"],
    )

    text = app.get_connections_analysis_text()

    assert "=== Verbindungen ===" in text
    assert "Proto: tcp" in text
    assert "Process: sshd" in text
    assert "systemd" not in text


def test_analyze_connections_with_chad_uses_formatted_text():
    app = App.__new__(App)
    calls = []
    app.conn_table = DummyConnTable(
        {
            "row1": ("tcp", "ESTAB", "127.0.0.1:22", "1.2.3.4:5555", "123", "sshd"),
        }
    )
    app.prepare_chad_analysis = lambda title, text: calls.append((title, text))

    app.analyze_connections_with_chad()

    assert calls
    assert calls[0][0] == "Verbindungen Analyse"
    assert "Proto: tcp" in calls[0][1]


def test_attach_connections_context_menu_source_matches_shared_actions():
    source = inspect.getsource(App.attach_connections_context_menu)

    assert 'label="Kopieren"' in source
    assert 'label="Einfügen"' in source
    assert 'label="Alles auswählen"' in source
    assert 'label="Auswahl an Chad Analyse senden"' in source
    assert 'label="Auswahl als Chad-Prompt kopieren"' in source
    assert "if row_id in current_selection" in source


def test_parse_arp_line_extracts_expected_fields():
    app = App.__new__(App)

    row = app.parse_arp_line(
        "_gateway (192.168.0.1) auf b8:c4:bc:bf:91:32 [ether] auf enp4s0"
    )

    assert row == {
        "host": "_gateway",
        "ip": "192.168.0.1",
        "mac": "b8:c4:bc:bf:91:32",
        "type": "ether",
        "iface": "enp4s0",
    }


def test_update_arp_table_replaces_rows_and_updates_status():
    app = App.__new__(App)
    app.tr = lambda _key, default=None: default or _key
    app.arp_table = DummyArpTable()
    app.arp_status_var = DummyVar("ARP: noch nicht geladen")

    app.update_arp_table(
        [
            {
                "host": "?",
                "ip": "172.17.0.2",
                "mac": "e6:ca:8e:b3:4d:a6",
                "iface": "docker0",
                "type": "ether",
            }
        ]
    )

    assert list(app.arp_table.rows.values()) == [
        ("?", "172.17.0.2", "e6:ca:8e:b3:4d:a6", "docker0", "ether")
    ]
    assert app.arp_status_var.get() == "ARP: 1 Einträge"
    assert app._arp_rows_cache == [
        {
            "host": "?",
            "ip": "172.17.0.2",
            "mac": "e6:ca:8e:b3:4d:a6",
            "iface": "docker0",
            "type": "ether",
        }
    ]


def test_arp_async_populates_connections_tab_without_logging(monkeypatch):
    app = App.__new__(App)
    calls = []
    logs = []
    callback_holder = {}

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            self.daemon = daemon

        def start(self):
            if self.target is not None:
                self.target()

    app.tab_conn = object()
    app.nb = type(
        "NotebookStub",
        (),
        {"select": lambda self, tab: calls.append(("select", tab))},
    )()
    app.tr = lambda _key, default=None: default or _key
    app.log = lambda message: logs.append(message)
    app.after = lambda _delay, callback: callback_holder.setdefault(
        "callback", callback
    )
    app.update_arp_table = lambda rows: calls.append(("update", rows))

    monkeypatch.setattr(
        app_module,
        "run_cmd",
        lambda args, timeout=0, text=True: (
            0,
            "? (172.17.0.2) auf e6:ca:8e:b3:4d:a6 [ether] auf docker0\n",
        ),
    )
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    app.arp_async()
    callback_holder["callback"]()

    assert calls[0] == ("select", app.tab_conn)
    assert calls[1] == (
        "update",
        [
            {
                "host": "?",
                "ip": "172.17.0.2",
                "mac": "e6:ca:8e:b3:4d:a6",
                "type": "ether",
                "iface": "docker0",
            }
        ],
    )
    assert logs == []


def test_parse_route_line_extracts_expected_fields():
    app = App.__new__(App)

    row = app.parse_route_line(
        "default via 192.168.0.1 dev enp4s0 proto dhcp metric 100"
    )

    assert row == {
        "dst": "default",
        "gateway": "192.168.0.1",
        "iface": "enp4s0",
        "src": "",
        "metric": "100",
        "raw": "default via 192.168.0.1 dev enp4s0 proto dhcp metric 100",
    }


def test_update_route_table_replaces_rows_and_updates_status():
    app = App.__new__(App)
    app.tr = lambda _key, default=None: default or _key
    app.route_table = DummyArpTable()
    app.route_status_var = DummyVar("Routing: noch nicht geladen")

    app.update_route_table(
        [
            {
                "dst": "default",
                "gateway": "192.168.0.1",
                "iface": "enp4s0",
                "src": "",
                "metric": "100",
                "raw": "default via 192.168.0.1 dev enp4s0 proto dhcp metric 100",
            }
        ]
    )

    assert list(app.route_table.rows.values()) == [
        (
            "default",
            "192.168.0.1",
            "enp4s0",
            "",
            "100",
        )
    ]
    assert app.route_status_var.get() == "Routing: 1 Einträge"
    assert app._route_rows_cache == [
        {
            "dst": "default",
            "gateway": "192.168.0.1",
            "iface": "enp4s0",
            "src": "",
            "metric": "100",
            "raw": "default via 192.168.0.1 dev enp4s0 proto dhcp metric 100",
        }
    ]


def test_update_route_table_sets_error_status_on_failure():
    app = App.__new__(App)
    app.tr = lambda _key, default=None: default or _key
    app.route_table = DummyArpTable()
    app.route_status_var = DummyVar("Routing: noch nicht geladen")

    app.update_route_table([], ok=False)

    assert app.route_status_var.get() == "Routing: Fehler beim Laden"


def test_route_async_populates_connections_tab_without_logging(monkeypatch):
    app = App.__new__(App)
    calls = []
    logs = []
    callback_holder = {}

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            self.daemon = daemon

        def start(self):
            if self.target is not None:
                self.target()

    app.tab_conn = object()
    app.nb = type(
        "NotebookStub",
        (),
        {"select": lambda self, tab: calls.append(("select", tab))},
    )()
    app.tr = lambda _key, default=None: default or _key
    app.log = lambda message: logs.append(message)
    app.after = lambda _delay, callback: callback_holder.setdefault(
        "callback", callback
    )
    app.update_route_table = lambda rows, ok=True: calls.append(("update", rows, ok))

    monkeypatch.setattr(
        app_module,
        "run_cmd",
        lambda args, timeout=0, text=True: (
            0,
            "default via 192.168.0.1 dev enp4s0 proto dhcp metric 100\n",
        ),
    )
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    app.route_async()
    callback_holder["callback"]()

    assert calls[0] == ("select", app.tab_conn)
    assert calls[1] == (
        "update",
        [
            {
                "dst": "default",
                "gateway": "192.168.0.1",
                "iface": "enp4s0",
                "src": "",
                "metric": "100",
                "raw": "default via 192.168.0.1 dev enp4s0 proto dhcp metric 100",
            }
        ],
        True,
    )
    assert logs == []
