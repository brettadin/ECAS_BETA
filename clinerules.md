# Cline Execution Rules

## Execute tools instead of describing them

- When asked to inspect, edit, or test code, perform the task using the actual tools available in the current Cline session.
- Never respond with a proposed tool call, raw JSON tool block, or a description of an action as a substitute for executing it.
- Use the exact tool names, arguments, and calling format provided by Cline's active system instructions.
- Do not invent tool names, tool results, file contents, or test results.
- After invoking a tool, wait for its actual result before deciding what to do next.
- If a tool is unavailable or fails, report the specific limitation or error.

## File editing

- Read a file before modifying it.
- Make the smallest change that satisfies the request.
- Preserve unrelated code and existing user changes.
- Do not reset Git, change branches, discard changes, or create unnecessary backups.
- After editing, inspect the changed code to verify the edit was applied.

## Testing

- Run the requested tests using the available terminal tool.
- Report the actual command and its actual output.
- Never claim that a test passed unless the command completed and its result confirms success.
- Do not modify unrelated code just to make tests pass.

## Completion reports

Report:
1. Files actually changed.
2. What changed.
3. Tests actually run and their results.
4. Any incomplete steps and the reason they could not be completed.

## Official Project Name

The official project name is **ECAS — Exoplanetary Characterization & Astrochemistry Suite**.

- Use this exact name whenever the full project name is needed.
- Use **ECAS** when the acronym alone is sufficient.
- Do not invent alternate expansions or rename the project in UI titles, documentation, comments, or generated code.
- Preserve the official name when creating or updating project files.