/** Build a simple text prompt from template parts. */
export function buildPrompt(parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join('\n')
}

/** Wrap user input in a standard instruction template. */
export function wrapInstruction(instruction: string, context?: string): string {
  if (!context) return instruction
  return `${context}\n\n---\n\n${instruction}`
}
