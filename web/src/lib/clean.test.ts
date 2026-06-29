import { describe, expect, it } from "vitest"

import { cleanGroundingTokens } from "@/lib/clean"

describe("cleanGroundingTokens", () => {
  it("returns empty string for empty input", () => {
    expect(cleanGroundingTokens("")).toBe("")
  })

  it("leaves plain markdown untouched", () => {
    const md = "# Title\n\nSome **bold** text."
    expect(cleanGroundingTokens(md)).toBe(md)
  })

  it("unwraps <|ref|> spans keeping inner text", () => {
    expect(cleanGroundingTokens("<|ref|>Hello world<|/ref|>")).toBe(
      "Hello world"
    )
  })

  it("drops <|det|> coordinate boxes entirely", () => {
    const input =
      "<|ref|>Invoice<|/ref|><|det|>[[10,20,30,40]]<|/det|>"
    expect(cleanGroundingTokens(input)).toBe("Invoice")
  })

  it("handles multiple grounded spans", () => {
    const input =
      "<|ref|>Line one<|/ref|><|det|>[[0,0,1,1]]<|/det|>\n" +
      "<|ref|>Line two<|/ref|><|det|>[[2,2,3,3]]<|/det|>"
    expect(cleanGroundingTokens(input)).toBe("Line one\nLine two")
  })

  it("handles multiline content inside a ref span", () => {
    const input = "<|ref|>first\nsecond<|/ref|>"
    expect(cleanGroundingTokens(input)).toBe("first\nsecond")
  })

  it("removes stray / unmatched grounding markers", () => {
    expect(cleanGroundingTokens("text <|ref|> more")).toBe("text  more")
    expect(cleanGroundingTokens("a<|/det|>b")).toBe("ab")
  })

  it("collapses blank lines left by removed boxes", () => {
    const input = "para one\n\n\n\npara two"
    expect(cleanGroundingTokens(input)).toBe("para one\n\npara two")
  })

  it("trims surrounding whitespace", () => {
    expect(cleanGroundingTokens("  \n hello \n  ")).toBe("hello")
  })
})
