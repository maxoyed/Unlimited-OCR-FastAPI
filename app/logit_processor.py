"""Embedded sglang custom-logit-processor payload (no sglang import needed).

The official Unlimited-OCR example sends a serialized custom logit processor so
the server applies DeepSeek-OCR's no-repeat n-gram suppression:

    "custom_logit_processor": DeepseekOCRNoRepeatNGramLogitProcessor.to_str()

``to_str()`` is defined (in sglang) as::

    json.dumps({"callable": dill.dumps(cls).hex()})

Because ``DeepseekOCRNoRepeatNGramLogitProcessor`` is importable on the sglang
server, ``dill.dumps(cls)`` serialises it **by reference** — the blob only
encodes the import path
``sglang.srt.sampling.custom_logit_processor.DeepseekOCRNoRepeatNGramLogitProcessor``,
which the server resolves to its real implementation at load time.

We therefore hardcode that exact serialized string here instead of importing
sglang (which would drag in torch and GPU deps). The pickle is a pure protocol-4
``STACK_GLOBAL`` reference:

    PROTO 4
    SHORT_BINUNICODE 'sglang.srt.sampling.custom_logit_processor'
    SHORT_BINUNICODE 'DeepseekOCRNoRepeatNGramLogitProcessor'
    STACK_GLOBAL
    STOP

To regenerate (e.g. if the class moves), run ``scripts/gen_logit_processor.py``.
"""

# json.dumps({"callable": dill.dumps(DeepseekOCRNoRepeatNGramLogitProcessor, byref=True).hex()})
CUSTOM_LOGIT_PROCESSOR: str = (
    '{"callable": "80049559000000000000008c2a73676c616e672e7372742e73616d'
    "706c696e672e637573746f6d5f6c6f6769745f70726f636573736f72948c26446565"
    "707365656b4f43524e6f5265706561744e4772616d4c6f67697450726f636573736f"
    '729493942e"}'
)

# Fixed n-gram size used by the official example.
NGRAM_SIZE: int = 35
