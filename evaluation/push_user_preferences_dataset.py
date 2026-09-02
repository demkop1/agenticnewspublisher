import os
import uuid

import dotenv
from langsmith import Client

dotenv.load_dotenv()

DATASET_NAME = os.environ.get("LANGSMITH_USER_PREFERENCES_DATASET", "news-user-preferences")

# Fixed namespace so re-running this script upserts the same rows instead of
# duplicating them (examples are keyed by a uuid5 of their preference text).
_ID_NAMESPACE = uuid.UUID("3f7f7bd0-8f0f-4b8f-9c62-9a6d4f6a2b71")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_PROJECT_ROOT, "user_profile.txt")) as f:
    _ORIGINAL_USER_PROFILE = f.read().strip()

USER_PREFERENCES = [
    _ORIGINAL_USER_PROFILE,
    "I am a financial news editor interested in publishing global stock market and economic policy news onto my channel.",
    "I am a tech journalist and want to curate the latest news on AI research and startups for my channel's audience.",
    "I am a sports news editor focused on publishing football (soccer) transfer news and match results onto my channel.",
    "I am a health news editor interested in publishing news about public health, pandemics, and medical breakthroughs onto my channel.",
    "I am a climate news editor and want to publish the latest news on climate change policy and natural disasters onto my channel.",
    "I am a political news editor interested in publishing news about elections and government policy changes in the European Union onto my channel.",
    "I am a crypto news editor focused on publishing breaking news about cryptocurrency regulation and blockchain technology onto my channel.",
    "I am an entertainment news editor interested in publishing celebrity news and major film industry announcements onto my channel.",
    "I am a security news editor and want to publish news about cybersecurity breaches and data privacy incidents onto my channel.",
]


def get_or_create_dataset(client: Client):
    if client.has_dataset(dataset_name=DATASET_NAME):
        return client.read_dataset(dataset_name=DATASET_NAME)
    return client.create_dataset(
        dataset_name=DATASET_NAME,
        description=(
            "Sample user preference profiles for evaluating the news "
            "orchestrator's search-query generation across topics."
        ),
    )


def push_examples(client: Client, dataset_id) -> None:
    examples = [
        {
            "id": str(uuid.uuid5(_ID_NAMESPACE, preference)),
            "inputs": {"user_profile": preference},
        }
        for preference in USER_PREFERENCES
    ]
    client.create_examples(dataset_id=dataset_id, examples=examples)


def main() -> None:
    client = Client()
    dataset = get_or_create_dataset(client)
    push_examples(client, dataset.id)
    print(f"Pushed {len(USER_PREFERENCES)} user preference examples to dataset '{DATASET_NAME}' ({dataset.id}).")


if __name__ == "__main__":
    main()
