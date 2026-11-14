"""Cyan Eclipse Routeseal - License Server licence gate (ETO-44).

Wraps the Cyan Eclipse License Server client library (ActivationClient,
the Folio L-3 / ACT pattern) and turns its named states into gate
decisions for Routeseal's priced boundary: sealing a dispatch
(routeseal_seal_dispatch, $0.25/op per PC-8). Reads, check, export
and recompute are never licence-gated, in any licence state.

Gate modes:
- enforced: a licence state file exists (artefact + install_id issued
  by the License Server, tenant #1 fixture scope); the gate activates
  once (install_id binding), then check-in at each priced call.
  Priced work runs only in LICENSE_VALID / LICENSE_GRACE. A revoked
  licence is refused at the next check-in.
- absent: no licence state file configured; priced work is refused
  with LICENSE_NOT_CONFIGURED. The gate never invents a licence.
Check-in presents the activation token and artefact hash only.
Fixture/test scope only: no real customer licences, no charges.
"""
import base64
import hashlib
import json
import os
import sys
import uuid

PRODUCT_ID = "routeseal"
PAID_BOUNDARY_FEATURE = "dispatch_seal"
UNIT_PRICE_MINOR = 25
PAID_STATES = ("LICENSE_VALID", "LICENSE_GRACE")


def artefact_hash(artefact):
    head = artefact.split(".", 1)[0]
    body = base64.urlsafe_b64decode(head + "=" * (-len(head) % 4))
    return hashlib.sha256(body).hexdigest()


def _load_activation_client(base_url):
    candidates = []
    env_dir = os.environ.get("CETLIC_CLIENT_DIR")
    if env_dir:
        candidates.append(env_dir)
    candidates.append("/home/witness/app-family/cyan-eclipse-license-server")
    sibling = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "cyan-eclipse-license-server")
    candidates.append(os.path.normpath(sibling))
    for cand in candidates:
        if os.path.isfile(os.path.join(cand, "client", "activation.py")):
            if cand not in sys.path:
                sys.path.insert(0, cand)
            try:
                from client.activation import ActivationClient
                return ActivationClient(base_url)
            except Exception:
                continue
    return None


class LicenceGate:
    """client: optional transport with the ActivationClient shape
    (activate / checkin), injected by tests; default loads the real
    License Server client library."""

    def __init__(self, state_path=None, base_url=None, client=None):
        self.state_path = state_path or os.environ.get(
            "ROUTESEAL_LICENCE_STATE")
        self.base_url = base_url or os.environ.get(
            "ROUTESEAL_LICENCE_SERVER", "http://127.0.0.1:8799")
        self._client = client
        self.state = None
        if self.state_path and os.path.isfile(self.state_path):
            with open(self.state_path, encoding="utf-8") as f:
                self.state = json.load(f)

    @property
    def mode(self):
        return "enforced" if self.state else "absent"

    def _save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.state, f)
        os.replace(tmp, self.state_path)

    def check(self):
        """Returns (allowed: bool, licence_state: str). Activation
        on first use, check-in thereafter."""
        if not self.state:
            return False, "LICENSE_NOT_CONFIGURED"
        client = self._client or _load_activation_client(self.base_url)
        if client is None:
            return False, "LICENSE_CLIENT_UNAVAILABLE"
        try:
            if not self.state.get("activation_token"):
                install_id = self.state.get("install_id") or str(uuid.uuid4())
                r = client.activate(self.state["artefact"], install_id,
                                    self.state.get("install_label", "routeseal"))
                if r.get("state") not in PAID_STATES:
                    return False, r.get("state", "LICENSE_UNKNOWN")
                self.state["install_id"] = install_id
                self.state["activation_token"] = r.get("activation_token")
                self.state["license_id"] = r.get("license_id")
                self.state["artefact_hash"] = artefact_hash(self.state["artefact"])
                self._save()
                return True, r["state"]
            r = client.checkin(self.state["activation_token"],
                               self.state["artefact_hash"])
            state = r.get("state", "LICENSE_UNKNOWN")
            return state in PAID_STATES, state
        except Exception as exc:
            return False, "LICENSE_SERVER_UNREACHABLE"
