"""Milestone 0, Task 0.2 - deterministic Student-ID salting."""
import hashlib
import json
import sys


def get_student_params(student_id: str):
    h = int(hashlib.sha256(student_id.encode("utf-8")).hexdigest()[:8], 16)
    # Salted matrix dimension N between 1024 and 1536 (multiple of 64)
    N = 1024 + ((h % 9) * 64)
    # Stride benchmark buffer: 2^24 float64 elements (~134 MB)
    buffer_elements = 16_777_216
    # Seed for deterministic random number generation
    seed = h % 100_007
    return {"student_id": student_id, "N": N,
            "buffer_elements": buffer_elements, "seed": seed}


if __name__ == "__main__":
    print(json.dumps(get_student_params(sys.argv[1]), indent=2))
