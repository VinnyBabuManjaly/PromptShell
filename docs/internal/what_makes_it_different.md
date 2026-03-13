What already exists (overlapping pieces)                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                    
  ┌────────────────────┬───────────────────────────────────────────────────┐                                                                                                                                                                                                        
  │      Product       │                  What it shares                   │                                                                                                                                                                                                        
  ├────────────────────┼───────────────────────────────────────────────────┤
  │ Warp Terminal      │ Terminal-aware AI, error context, command history │
  ├────────────────────┼───────────────────────────────────────────────────┤                                                                                                                                                                                                        
  │ GitHub Copilot CLI │ Terminal context capture, directory/git awareness │                                                                                                                                                                                                        
  ├────────────────────┼───────────────────────────────────────────────────┤                                                                                                                                                                                                        
  │ Matrix AI          │ Global hotkey → AI daemon                         │                                                                                                                                                                                                        
  ├────────────────────┼───────────────────────────────────────────────────┤
  │ TmuxAI             │ Reads tmux terminal state in real-time            │
  ├────────────────────┼───────────────────────────────────────────────────┤
  │ Wispr Flow         │ Voice dictation in any app including terminal     │
  └────────────────────┴───────────────────────────────────────────────────┘

  ---
  What doesn't exist as a single product

  No tool combines all three of these together:

  1. Hotkey-triggered daemon that snapshots full terminal state automatically (buffer + CWD + git + exit codes + error patterns)
  2. Voice input captured and fused with that context
  3. LLM synthesis step that rewrites vague intent → precise actionable prompt → clipboard (without replacing your terminal/IDE)

  The closest combo would be Warp + Matrix AI + Wispr Flow running together — but that's three tools, not one pipeline, and they don't share context with each other.

  ---
  The real differentiator

  Most tools are conversational (you type, they respond) or IDE-embedded. prompt-shell is a passive daemon that enhances intent — you stay in your workflow, hit a hotkey, speak vaguely, and get a precise prompt back. That synthesis step (vague → precise) is what nothing else
  does.

  So: the pieces exist, but the combination doesn't. That's a defensible niche.