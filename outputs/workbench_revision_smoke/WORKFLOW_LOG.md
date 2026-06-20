# Mini-Codex Workflow Log

- Created: 2026-06-19T16:24:56.290500+00:00
- Mode: mock_test
- User request: Add a generation history table. Revision request: keep tests offline and make history table explicit.

## Selected Files
- `app.py` sha256 `e0d98ef21c26c25f75bee99fbf46080f67c8f30caf7db1c142af9293150e88c8`
- `experiment_store.py` sha256 `e13b93e798d2763f08a730612cf063748d2405106264bae4d87d426fa395c6a5`
- `llm_client.py` sha256 `f272c8f19450a3d2189a5c5bed57627f9ea8d6bb70c4298c704b8e635ae8dd4b`
- `README.md` sha256 `119a1d060eb301630b04289debe2b119ced25fc9cc93537a88671fd97b3455b5`
- `tests/test_basic.py` sha256 `c90962cb75b3eeded5b23c0cf3893a1f639aff3403f852a2dfae4e228674631f`

## Proposed Change

Add generation history table.

## Files
- `app.py`: Implement request: Add generation history table.
- `experiment_store.py`: Implement request: Add generation history table.
- `tests/test_basic.py`: Implement request: Add generation history table.

## Diffs

### app.py

```diff
--- a/app.py
+++ b/app.py
@@ -2,7 +2,7 @@
 
 import streamlit as st
 
-from experiment_store import create_record
+from experiment_store import create_record, add_record, history_to_table
 from llm_client import generate_response
 
 
@@ -26,3 +26,16 @@
 latest_record = create_record(prompt, response, model_name=model_name)
 st.caption(f"Current record model: {latest_record['model_name']}")
 
+if "history" not in st.session_state:
+    st.session_state["history"] = []
+
+if generate:
+    st.session_state["history"] = add_record(st.session_state["history"], prompt, response)
+
+st.subheader("Generation history")
+rows = history_to_table(st.session_state["history"])
+if rows:
+    st.dataframe(rows, use_container_width=True)
+else:
+    st.caption("No generations yet.")
+
```

### experiment_store.py

```diff
--- a/experiment_store.py
+++ b/experiment_store.py
@@ -11,3 +11,21 @@
         "created_at": datetime.now(timezone.utc).isoformat(),
     }
 
+
+def add_record(history: list[dict[str, str]], prompt: str, response: str, model_name: str = "mock-local") -> list[dict[str, str]]:
+    if not response:
+        return list(history)
+    return [*history, create_record(prompt, response, model_name=model_name)]
+
+
+def history_to_table(history: list[dict[str, str]]) -> list[dict[str, str]]:
+    return [
+        {
+            "prompt": item.get("prompt", ""),
+            "response": item.get("response", ""),
+            "model_name": item.get("model_name", ""),
+            "created_at": item.get("created_at", ""),
+        }
+        for item in history
+    ]
+
```

### tests/test_basic.py

```diff
--- a/tests/test_basic.py
+++ b/tests/test_basic.py
@@ -2,7 +2,7 @@
 
 import unittest
 
-from experiment_store import create_record
+from experiment_store import create_record, add_record, history_to_table
 from llm_client import generate_response
 
 
@@ -18,6 +18,12 @@
         self.assertEqual(record["response"], "response")
         self.assertEqual(record["model_name"], "mock")
 
+    def test_history_records_prompt_and_response(self) -> None:
+        rows = add_record([], "prompt", "response", model_name="mock")
+        table = history_to_table(rows)
+        self.assertEqual(table[0]["prompt"], "prompt")
+        self.assertEqual(table[0]["response"], "response")
+
 
 if __name__ == "__main__":
     unittest.main()
```
