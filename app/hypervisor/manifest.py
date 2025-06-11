import os
import json
import logging

from typing import Dict, Any, Optional, List

from misc import parse_version, parse_revision, validate_model, download_file, check_platform

PLATFORM = check_platform()
MANIFEST_URL = "https://depot.moondream.ai/station/md_station_manifest_ubuntu.json"
MODEL_SIZE = "2B"


class Manifest:

    def __init__(self, path: Optional[str] = None, url: Optional[str] = None):
        self.logger = logging.getLogger("hypervisor")
        self.data = {}

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = path or os.path.join(base_dir, "data", "manifest.json")
        self.url = url or MANIFEST_URL
        self.update()

    def load(self):
        if not os.path.exists(self.path):
            self.update()
        else:
            self.logger.debug(f"Loading manifest from {self.path}")
            self._load_local()

    def update(self):
        if os.path.exists(self.url) or not (self.url.startswith('http://') or self.url.startswith('https://')):
            self.logger.debug(f"Using local manifest from {self.url}")
            self.path = self.url
        else:
            self.logger.debug(f"Downloading manifest from {self.url} to {self.path}")
            self._download()
        self.logger.debug(f"Loading manifest from {self.path}")
        self._load_local()

    def _load_local(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r") as f:
                self.data = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading manifest: {e}")

    def _download(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)

            download_file(self.url, self.path, self.logger)
        except Exception as e:
            self.logger.error(f"Error downloading manifest: {e}")
            print("error downloading manifest")

    def save(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving manifest: {e}")
            return False

    @property
    def version(self) -> str:
        return self.data.get("manifest_version", "")

    @property
    def date(self) -> str:
        return self.data.get("manifest_date", "")

    @property
    def current_bootstrap(self) -> Dict[str, str]:
        return self.data.get("current_bootstrap", {})

    @property
    def current_hypervisor(self) -> Dict[str, str]:
        return self.data.get("current_hypervisor", {})

    @property
    def current_cli(self) -> Dict[str, str]:
        return self.data.get("current_cli", {})

    def get_model(self, revision: str) -> Optional[Dict[str, Any]]:
        """Get model data with HF existence check."""
        model_data = self.models.get(revision)
        if not model_data:
            return None
        
        model_name, revision = validate_model(model_data.get("model_name"))
        logging.debug(f"Getting model {model_name} with revision {revision}")
        
        return {
            "revision": revision,
            "model": model_data,
            "model_name": model_name
        }

    @property
    def models(self) -> Dict[str, Dict[str, Any]]:
        return self.data.get("models", {})  # Return ALL families, not just MODEL_SIZE

    @property
    def latest_model(self):
        models_dict = self.models
        if not models_dict:
            return None
        
        # Iterate through ALL families (2B, 7B, etc.)
        all_models = {}
        for family_name, family_models in models_dict.items():
            for outer_key, model_data in family_models.items():
                revision = model_data.get("revision", outer_key)
                all_models[revision] = (outer_key, model_data, family_name)
        
        if not all_models:
            return None
        
        # Group by numeric components
        grouped = {}
        for rev in all_models.keys():
            numeric = parse_revision(rev)
            grouped.setdefault(numeric, []).append(rev)
        
        if not grouped:
            return None
        
        # Find latest with preferences
        latest_numeric = max(grouped.keys())
        candidates = grouped[latest_numeric]
        
        chosen = None
        for rev in candidates:
            if "4bit" in rev:
                chosen = rev
                break
        if not chosen:
            for rev in candidates:
                if all(c.isdigit() or c == "-" for c in rev):
                    chosen = rev
                    break
        if not chosen:
            chosen = candidates[0]
        
        # Now we properly unpack 3 elements including family_name
        outer_key, model_data, family_name = all_models[chosen]
        return model_data
    
    def get_inference_client(self, version: str) -> Optional[Dict[str, str]]:
        return self.data.get("inference_clients", {}).get(version, None)

    @property
    def inference_clients(self) -> Dict[str, Dict[str, str]]:
        return self.data.get("inference_clients", None)

    @property
    def latest_inference_client(self) -> Dict[str, Any]:
        inference_clients_dict = self.inference_clients
        if not inference_clients_dict:
            None

        version = max(inference_clients_dict.keys(), key=parse_version)
        return {
            "version": version,
            "inference_client": self.get_inference_client(version),
        }

    @property
    def notes(self) -> List[str]:
        return self.data.get("notes", [])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manifest = Manifest()
    print(f"Manifest version: {manifest.version}")
    print(f"Available models: {list(manifest.models.keys())}")
    print(f"Available inf clients {list(manifest.inference_clients.keys())}")
