"""Regenerate the embedded custom-logit-processor string in app/logit_processor.py.

The sglang server expects the value of
``DeepseekOCRNoRepeatNGramLogitProcessor.to_str()``, i.e.::

    json.dumps({"callable": dill.dumps(cls).hex()})

On a host where sglang is installed that serialises the class *by reference*
(the blob just encodes the import path, which the server resolves to its real
implementation). We reproduce that exact by-reference blob here WITHOUT
installing sglang/torch, by registering a placeholder under the same import
path and forcing ``byref=True``.

Usage:
    pip install dill
    python scripts/gen_logit_processor.py
"""

import json
import sys
import types

import dill

MODPATH = "sglang.srt.sampling.custom_logit_processor"
QUALNAME = "DeepseekOCRNoRepeatNGramLogitProcessor"


def main() -> None:
    for name in ["sglang", "sglang.srt", "sglang.srt.sampling", MODPATH]:
        sys.modules.setdefault(name, types.ModuleType(name))

    placeholder = type(QUALNAME, (), {})
    placeholder.__module__ = MODPATH
    placeholder.__qualname__ = QUALNAME
    sys.modules[MODPATH].__dict__[QUALNAME] = placeholder

    blob = dill.dumps(placeholder, byref=True)
    # Sanity check: a pure by-reference blob resolves back to the same object.
    assert dill.loads(blob) is placeholder, "expected a by-reference pickle"

    print(json.dumps({"callable": blob.hex()}))


if __name__ == "__main__":
    main()
