import os
import random
from collections import defaultdict

from datasets import load_dataset, Audio
from utils import validate_dataset


instructions = [
    "Based on this audio, count the number of phonemes in the corresponding utterance. Please write in Arabic numerals.",
    "Please count the number of phonemes in this audio. Use Arabic numbers for your answer.",
    "Determine the number of phonemes in the given utterance. Write your answer in numbers.",
    "Identify the number of phonemes in this audio file. Use Arabic digits.",
    "Listen to the audio and count the number of phonemes present. Write in digits.",
    "Calculate the total number of phonemes in this audio clip. Please use Arabic numerals.",
    "From the audio, ascertain the number of phonemes in the utterance. Write in Arabic numbers.",
    "Count how many phonemes you hear in this audio. Use numbers for your response.",
    "Please determine the number of phonemes in the audio provided. Write in Arabic digits.",
    "Identify and count the phonemes in this audio sample. Use digits.",
    "Based on this audio, identify the number of phonemes. Write in Arabic numerals.",
    "Calculate the number of phonemes in the provided audio. Use Arabic numbers.",
    "Listen and count the phonemes in this audio recording. Write your answer in numbers.",
    "Count the phonemes present in this given audio file. Use Arabic digits.",
    "Identify the total phonemes in this audio clip. Write in digits.",
    "Determine and count the number of phonemes in the provided audio. Use Arabic numerals.",
    "Based on the audio clip, calculate the number of phonemes. Write in numbers.",
    "Count the total number of phonemes in the given audio sample. Use Arabic numbers.",
    "Listen to the audio and determine the number of phonemes. Write in Arabic digits.",
    "Identify the number of phonemes in the provided audio recording. Use digits."
]

if __name__ == "__main__":
    ds = load_dataset(
        "speech31/voxangeles",
        cache_dir="datasets_cache",
        revision="refs/convert/parquet",
    )
    new_ds = ds["test"]

    def calculate_length(sample):
        sample["label"] = len(sample["phn"].split())
        return sample

    new_ds = new_ds.map(calculate_length, num_proc=32)

    # Filter out samples with length
    new_ds = new_ds.filter(lambda sample: 1 < sample["label"] <= 10)

    # Filter out samples longer than 2 seconds
    new_ds = new_ds.filter(lambda sample: len(sample["audio"]["array"]) / sample["audio"]["sampling_rate"] <= 2)

    # Categorize the samples by their lengths
    length_categories = defaultdict(list)
    for i, sample in enumerate(new_ds):
        length_categories[sample["label"]].append(i)

    # Randomly select 60% of the samples for each length
    selected_indices = []
    for i, (length, indices) in enumerate(sorted(length_categories.items())):
        num_to_select = int(len(indices) * 0.6)
        random.seed(i)
        selected_indices.extend(random.sample(indices, num_to_select))

    # Create a new dataset with the selected indices
    new_ds = new_ds.select(selected_indices)

    # Reformatting
    def _map(sample, index):
        return {
            "audio": sample["audio"],
            "file": sample["file"],
            "instruction": instructions[index % len(instructions)],
            "label": sample["label"],
        }
    new_ds = new_ds.map(_map, with_indices=True, remove_columns=ds["test"].column_names, num_proc=32)
    new_ds = new_ds.cast_column("audio", Audio(sampling_rate=16_000))

    # Validate & Push
    validate_dataset(new_ds)
    new_ds.push_to_hub(repo_id="speech31/PhoneSegmentCounting_VoxAngeles", split="test", token=os.environ["HF_TOKEN"])
