from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import hopsworks

class FraudDatasetSize(Enum):
    LARGE = "LARGE"
    MEDIUM = "MEDIUM"
    SMALL = "SMALL"


class HopsworksSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    MLFS_DIR: Path = Path(__file__).parent

    # For hopsworks.login(), set as environment variables if they are not already set as env variables
    HOPSWORKS_API_KEY: SecretStr | None = None
    HOPSWORKS_PROJECT: str | None = None
    HOPSWORKS_HOST: str | None = None

    # Air Quality
    AQICN_API_KEY: SecretStr | None = None

    # GitHub
    GH_PAT: SecretStr | None = None
    GH_USERNAME: SecretStr | None = None
    
    # Other API Keys
    FELDERA_API_KEY: SecretStr | None = None    
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_MODEL_ID: str = "gpt-4o-mini"


    # Feature engineering
    FRAUD_DATA_SIZE: FraudDatasetSize = FraudDatasetSize.SMALL
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Personalized Recommendations
    TWO_TOWER_MODEL_EMBEDDING_SIZE: int = 16
    TWO_TOWER_MODEL_BATCH_SIZE: int = 2048
    TWO_TOWER_NUM_EPOCHS: int = 10
    TWO_TOWER_WEIGHT_DECAY: float = 0.001
    TWO_TOWER_LEARNING_RATE: float = 0.01
    TWO_TOWER_DATASET_VALIDATON_SPLIT_SIZE: float = 0.1
    TWO_TOWER_DATASET_TEST_SPLIT_SIZE: float = 0.1

    RANKING_DATASET_VALIDATON_SPLIT_SIZE: float = 0.1
    RANKING_LEARNING_RATE: float = 0.2
    RANKING_ITERATIONS: int = 100
    RANKING_SCALE_POS_WEIGHT: int = 10
    RANKING_EARLY_STOPPING_ROUNDS: int = 5

    # Inference
    RANKING_MODEL_TYPE: Literal["ranking", "llmranking"] = "ranking"
    CUSTOM_HOPSWORKS_INFERENCE_ENV: str = "custom_env_name"

    # def load_hopsworks_secrets_if_missing(self):
    #     """Load missing secrets only when running inside a Hopsworks Job."""
        
    #     # Detect Hopsworks Job runtime
    #     if "HOPSWORKS_JOB_ID" not in os.environ:
    #         return self  # Do nothing locally or in Jupyter

    #     try:
    #         secrets_api = hopsworks.get_secrets_api()
    #     except Exception:
    #         return self

    #     def load(name):
    #         try:
    #             secret = secrets_api.get_secret(name)
    #             return secret.value if secret else None
    #         except Exception:
    #             return None

    #     if self.HOPSWORKS_API_KEY is None:
    #         val = load("HOPSWORKS_API_KEY")
    #         if val:
    #             self.HOPSWORKS_API_KEY = SecretStr(val)

    #     if self.AQICN_API_KEY is None:
    #         val = load("AQICN_API_KEY")
    #         if val:
    #             self.AQICN_API_KEY = SecretStr(val)

    #     if self.GH_PAT is None:
    #         val = load("GH_PAT")
    #         if val:
    #             self.GH_PAT = SecretStr(val)

    #     if self.GH_USERNAME is None:
    #         val = load("GH_USERNAME")
    #         if val:
    #             self.GH_USERNAME = SecretStr(val)

    #     return self

    # def model_post_init(self, __context):
    #     """Runs after the model is initialized."""
    #     print("HopsworksSettings initialized!")

    #     # load missing secrets from hopsworks
    #     self.load_hopsworks_secrets_if_missing()



    #     # # Set environment variables if not already set
    #     # if os.getenv("HOPSWORKS_API_KEY") is None:
    #     #     if self.HOPSWORKS_API_KEY is not None:
    #     #         os.environ['HOPSWORKS_API_KEY'] = self.HOPSWORKS_API_KEY.get_secret_value()
    #     # if os.getenv("HOPSWORKS_PROJECT") is None:
    #     #     if self.HOPSWORKS_PROJECT is not None:
    #     #         os.environ['HOPSWORKS_PROJECT'] = self.HOPSWORKS_PROJECT
    #     # if os.getenv("HOPSWORKS_HOST") is None:
    #     #     if self.HOPSWORKS_HOST is not None:
    #     #         os.environ['HOPSWORKS_HOST'] = self.HOPSWORKS_HOST

    #     # --- Check required .env values ---
    #     missing = []
    #     # 1. HOPSWORKS_API_KEY
    #     api_key = self.HOPSWORKS_API_KEY or os.getenv("HOPSWORKS_API_KEY")
    #     if not api_key:
    #         missing.append("HOPSWORKS_API_KEY")
    #     # 2. AQICN_API_KEY
    #     aqicn_api_key = self.AQICN_API_KEY or os.getenv("AQICN_API_KEY")
    #     if not aqicn_api_key:
    #         missing.append("AQICN_API_KEY")
    #     # 3. GITHUB_PAT
    #     github_pat = self.GH_PAT or os.getenv("GH_PAT")
    #     if not github_pat:
    #         missing.append("GH_PAT")
    #     # 4. GITHUB_USERNAME
    #     github_username = self.GH_USERNAME or os.getenv("GH_USERNAME")
    #     if not github_username:
    #         missing.append("GH_USERNAME")

    #     if missing:
    #         raise ValueError(
    #             "The following required settings are missing from your environment (.env or system):\n  " +
    #             "\n  ".join(missing)
    #         )