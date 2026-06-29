/**
 * Strip Unlimited-OCR grounding tokens to yield clean markdown.
 *
 * The model emits grounded output of the form:
 *
 *   <|ref|>visible text<|/ref|><|det|>[[x1,y1,x2,y2]]<|/det|>
 *
 * where ``<|ref|>…<|/ref|>`` wraps the recognised text and
 * ``<|det|>…<|/det|>`` holds its bounding-box coordinates. For a readable demo
 * we unwrap the ref content and drop the det boxes entirely.
 */
export function cleanGroundingTokens(text: string): string {
  if (!text) return ""

  return (
    text
      // Drop coordinate boxes completely (do this before unwrapping refs).
      .replace(/<\|det\|>[\s\S]*?<\|\/det\|>/g, "")
      // Unwrap recognised-text spans, keeping their inner content.
      .replace(/<\|ref\|>([\s\S]*?)<\|\/ref\|>/g, "$1")
      // Remove any stray / unmatched grounding markers defensively.
      .replace(/<\|\/?(?:ref|det)\|>/g, "")
      // Collapse blank lines left behind by removed boxes.
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim()
  )
}
