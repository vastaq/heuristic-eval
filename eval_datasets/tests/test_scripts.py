import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "eval_datasets" / "scripts"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class ScriptTests(unittest.TestCase):
    def test_export_preserves_legacy_asserts_and_filters_to_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "dataset.json"
            output = Path(tmp) / "tests.yaml"
            write_json(
                dataset,
                {
                    "version": "v1",
                    "project": "demo",
                    "dataset_type": "character_prompt_eval",
                    "records": [
                        {
                            "id": "demo_accepted_001",
                            "layer": "core_smoke",
                            "role": "demo",
                            "character_context": "file://prompt.md",
                            "scene_type": "identity",
                            "difficulty": "easy",
                            "input": "你是谁？",
                            "target_behavior": ["直接回答身份"],
                            "avoid_behavior": ["回避身份"],
                            "tags": ["identity"],
                            "rubric_ref": "identity",
                            "source_path": "demo/test.yaml",
                            "review_status": "accepted",
                            "legacy_asserts": [
                                {"type": "llm-rubric", "value": "直接回答身份"},
                                {"type": "icontains", "value": "Demo"},
                            ],
                        },
                        {
                            "id": "demo_candidate_001",
                            "layer": "core_smoke",
                            "role": "demo",
                            "character_context": "file://prompt.md",
                            "scene_type": "identity",
                            "difficulty": "easy",
                            "input": "候选样例",
                            "target_behavior": ["可判断"],
                            "avoid_behavior": ["不可判断"],
                            "tags": ["candidate"],
                            "rubric_ref": "identity",
                            "source_path": "demo/test.yaml",
                            "review_status": "candidate",
                        },
                    ],
                },
            )

            result = run_script("export_promptfoo_tests.py", str(dataset), str(output))

            self.assertEqual(result.returncode, 0, result.stderr)
            exported = output.read_text(encoding="utf-8")
            self.assertIn("demo_accepted_001", exported)
            self.assertNotIn("demo_candidate_001", exported)
            self.assertIn("source_path: demo/test.yaml", exported)
            self.assertIn("type: icontains", exported)
            self.assertIn("value: Demo", exported)

    def test_import_promptfoo_yaml_preserves_metadata_and_asserts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "legacy.yaml"
            output = Path(tmp) / "seed.json"
            source.write_text(
                """
- vars:
    character_context: file://prompt.md
    question: "Slowpoke, who are you?"
  metadata:
    id: slowpoke_identity_001
    layer: core_smoke
    role: slowpoke
    scene_type: boundary_and_identity
    difficulty: easy
    tags: [identity, child]
  assert:
    - type: llm-rubric
      value: "The reply should answer in first person."
""".strip(),
                encoding="utf-8",
            )

            result = run_script(
                "import_promptfoo_tests.py",
                str(source),
                str(output),
                "--project",
                "slowpoke",
                "--role",
                "slowpoke",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            imported = json.loads(output.read_text(encoding="utf-8"))
            record = imported["records"][0]
            self.assertEqual(record["id"], "slowpoke_identity_001")
            self.assertEqual(record["input"], "Slowpoke, who are you?")
            self.assertTrue(record["source_path"].endswith("legacy.yaml"))
            self.assertEqual(record["legacy_asserts"][0]["type"], "llm-rubric")
            self.assertEqual(record["review_status"], "candidate")

    def test_import_and_export_preserve_input_var_and_extra_vars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "legacy.yaml"
            seed = Path(tmp) / "seed.json"
            exported = Path(tmp) / "exported.yaml"
            source.write_text(
                """
- vars:
    user_input: "你是谁呀？"
    behaviour_context: file://shared.md
    character_context: file://prompt.md
  metadata:
    conversationId: c1
  assert:
    - type: icontains
      value: 奥特曼
- vars:
    user_input: "下一句"
  metadata:
    conversationId: c1
  assert:
    - type: llm-rubric
      value: "应该接住上文"
""".strip(),
                encoding="utf-8",
            )

            imported = run_script(
                "import_promptfoo_tests.py",
                str(source),
                str(seed),
                "--project",
                "dou",
                "--role",
                "ultraman",
            )
            self.assertEqual(imported.returncode, 0, imported.stderr)
            payload = json.loads(seed.read_text(encoding="utf-8"))
            first, second = payload["records"]
            self.assertEqual(first["input_var"], "user_input")
            self.assertEqual(first["vars"]["behaviour_context"], "file://shared.md")
            self.assertEqual(first["turn"], 1)
            self.assertEqual(second["turn"], 2)

            for record in payload["records"]:
                record["review_status"] = "accepted"
            write_json(seed, payload)

            result = run_script("export_promptfoo_tests.py", str(seed), str(exported))
            self.assertEqual(result.returncode, 0, result.stderr)
            text = exported.read_text(encoding="utf-8")
            self.assertIn("user_input: 你是谁呀？", text)
            self.assertIn("behaviour_context: file://shared.md", text)
            self.assertNotIn("question: 你是谁呀？", text)

    def test_audit_strict_flags_duplicate_ids_and_concentrated_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "dataset.json"
            base_record = {
                "id": "dup",
                "layer": "core_smoke",
                "role": "demo",
                "character_context": "file://prompt.md",
                "scene_type": "identity",
                "difficulty": "easy",
                "input": "hello",
                "target_behavior": ["answer"],
                "avoid_behavior": ["ignore"],
                "tags": ["identity"],
                "rubric_ref": "identity",
                "source_path": "demo/test.yaml",
                "review_status": "accepted",
            }
            write_json(
                dataset,
                {
                    "version": "v1",
                    "project": "demo",
                    "dataset_type": "character_prompt_eval",
                    "records": [base_record, dict(base_record)],
                },
            )

            result = run_script("audit_testset_balance.py", str(dataset), "--strict")

            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate id: dup", result.stdout)
            self.assertIn("tag 'identity' appears in 2/2", result.stdout)

    def test_batch_import_discovers_multiple_test_yaml_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "role_a").mkdir()
            (root / "role_b").mkdir()
            (root / "role_empty").mkdir()
            (root / "role_a" / "test_daily.yaml").write_text(
                """
- vars:
    question: "hello"
  assert:
    - type: llm-rubric
      value: "answer"
""".strip(),
                encoding="utf-8",
            )
            (root / "role_b" / "test.yaml").write_text(
                """
- vars:
    user_input: "你好"
  assert:
    - type: icontains
      value: 你好
""".strip(),
                encoding="utf-8",
            )
            (root / "role_empty" / "test_empty.yaml").write_text("", encoding="utf-8")
            output = root / "all.json"

            result = run_script(
                "batch_import_test_yaml.py",
                str(root),
                str(output),
                "--project",
                "all_existing_roles",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["source_paths"]), 3)
            self.assertEqual(len(payload["records"]), 2)
            self.assertEqual({record["role"] for record in payload["records"]}, {"role_a", "role_b"})

    def test_init_eval_run_creates_thin_intake_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"

            result = run_script(
                "init_eval_run.py",
                "--run-id",
                "demo_run",
                "--project",
                "demo",
                "--output-dir",
                str(output),
                "--source-root",
                "local/out",
                "--source-file",
                "summary=local/out/summary.json",
                "--controlled-variable",
                "season",
                "--content-unit",
                "forest",
                "--case-count",
                "4",
                "--success-count",
                "3",
                "--failure-count",
                "1",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            decision = json.loads((output / "decision.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["run_id"], "demo_run")
            self.assertEqual(manifest["project"], "demo")
            self.assertEqual(manifest["source_artifact_root"], "local/out")
            self.assertEqual(manifest["source_files"], {"summary": "local/out/summary.json"})
            self.assertEqual(manifest["source_files"]["summary"], "local/out/summary.json")
            self.assertEqual(manifest["controlled_variables"], ["season"])
            self.assertEqual(manifest["content_units"], ["forest"])
            self.assertEqual(manifest["case_count"], 4)
            self.assertEqual(manifest["success_count"], 3)
            self.assertEqual(manifest["failure_count"], 1)
            self.assertEqual(decision["decision_id"], "demo_run_decision")
            self.assertEqual(decision["decision_type"], "needs_decision")
            self.assertIsNone(decision["accepted_direction"])
            self.assertEqual((output / "human_signals.jsonl").read_text(encoding="utf-8"), "")

    def test_init_eval_run_marks_accept_direction_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"

            result = run_script(
                "init_eval_run.py",
                "--run-id",
                "demo_run",
                "--project",
                "demo",
                "--output-dir",
                str(output),
                "--decision-type",
                "accept_direction",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads((output / "decision.json").read_text(encoding="utf-8"))
            self.assertEqual(decision["decision_type"], "accept_direction")
            self.assertIs(decision["accepted_direction"], True)

    def test_init_eval_run_does_not_accept_non_accept_decisions_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"

            result = run_script(
                "init_eval_run.py",
                "--run-id",
                "demo_run",
                "--project",
                "demo",
                "--output-dir",
                str(output),
                "--decision-type",
                "revise_prompt_boundary",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads((output / "decision.json").read_text(encoding="utf-8"))
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertIsNone(decision["accepted_direction"])
            self.assertEqual(manifest["source_files"], {})

    def test_batch_import_filters_roles_and_maps_scene_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "star").mkdir()
            (root / "vampire").mkdir()
            for role in ("star", "vampire"):
                (root / role / "test.yaml").write_text(
                    f"""
- vars:
    question: "hello"
  metadata:
    role: {role}
    scene: greeting
  assert:
    - type: llm-rubric
      value: "answer naturally"
""".strip(),
                    encoding="utf-8",
                )
            output = root / "filtered.json"

            result = run_script(
                "batch_import_test_yaml.py",
                str(root),
                str(output),
                "--project",
                "demo",
                "--include-role",
                "star",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["records"]), 1)
            self.assertEqual(payload["records"][0]["role"], "star")
            self.assertEqual(payload["records"][0]["scene_type"], "greeting")
            self.assertEqual(len(payload["filtered"]), 1)

    def test_select_hl_pilot_candidates_filters_and_caps_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "dataset.json"
            output = Path(tmp) / "review_batch.json"
            write_json(
                dataset,
                {
                    "version": "v1",
                    "project": "demo",
                    "dataset_type": "character_prompt_eval",
                    "records": [
                        {
                            "id": "cook_context_001",
                            "layer": "context_drift",
                            "role": "cook",
                            "character_context": "file://cook.md",
                            "scene_type": "emotion_to_practical",
                            "difficulty": "medium",
                            "input": "现在给我一个很小的动作。",
                            "target_behavior": ["shift to one action"],
                            "avoid_behavior": ["long plan"],
                            "tags": ["multi"],
                            "rubric_ref": "context",
                            "source_path": "demo/test.yaml",
                            "source_index": 4,
                            "review_status": "candidate",
                            "conversation_id": "c1",
                            "turn": 2,
                            "legacy_asserts": [{"type": "llm-rubric", "value": "one action"}],
                        },
                        {
                            "id": "dreamer_identity_001",
                            "layer": "identity_boundary",
                            "role": "dreamer",
                            "character_context": "file://dreamer.md",
                            "scene_type": "brief_identity",
                            "difficulty": "easy",
                            "input": "你是谁？一句话。",
                            "target_behavior": ["brief answer"],
                            "avoid_behavior": ["long intro"],
                            "tags": ["single"],
                            "rubric_ref": "identity",
                            "source_path": "demo/test.yaml",
                            "review_status": "candidate",
                        },
                        {
                            "id": "star_context_001",
                            "layer": "context_drift",
                            "role": "star",
                            "character_context": "file://star.md",
                            "scene_type": "emotion_to_practical",
                            "difficulty": "medium",
                            "input": "给我一步。",
                            "target_behavior": ["one step"],
                            "avoid_behavior": ["lecture"],
                            "tags": [],
                            "rubric_ref": "context",
                            "source_path": "demo/test.yaml",
                            "review_status": "candidate",
                        },
                    ],
                },
            )

            result = run_script(
                "select_hl_pilot_candidates.py",
                str(dataset),
                str(output),
                "--role",
                "cook",
                "--role",
                "dreamer",
                "--max-records",
                "1",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_dataset"], str(dataset))
            self.assertEqual(payload["selection"]["roles"], ["cook", "dreamer"])
            self.assertEqual(payload["selection"]["max_records"], 1)
            self.assertEqual(len(payload["records"]), 1)
            selected = payload["records"][0]
            self.assertEqual(selected["id"], "cook_context_001")
            self.assertEqual(selected["source_index"], 4)
            self.assertEqual(selected["legacy_asserts"][0]["type"], "llm-rubric")
            self.assertEqual(selected["conversation_id"], "c1")

    def test_select_hl_pilot_candidates_handles_missing_optional_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "dataset.json"
            output = Path(tmp) / "review_batch.json"
            write_json(
                dataset,
                {
                    "version": "v1",
                    "project": "demo",
                    "dataset_type": "character_prompt_eval",
                    "records": [
                        {
                            "id": "cook_minimal_001",
                            "layer": "micro_narrative",
                            "role": "cook",
                            "scene_type": "ordinary_frustration",
                            "difficulty": "medium",
                            "input": "今天有点烦。",
                            "target_behavior": ["receive feeling"],
                            "avoid_behavior": ["generic comfort"],
                            "tags": [],
                            "rubric_ref": "emotional_reception",
                            "source_path": "demo/test.yaml",
                            "review_status": "candidate",
                        }
                    ],
                },
            )

            result = run_script(
                "select_hl_pilot_candidates.py",
                str(dataset),
                str(output),
                "--role",
                "cook",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["records"][0]["id"], "cook_minimal_001")

    def test_select_hl_pilot_candidates_balances_requested_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "dataset.json"
            output = Path(tmp) / "review_batch.json"
            records = []
            for index in range(3):
                records.append(
                    {
                        "id": f"cook_{index}",
                        "layer": "context_drift",
                        "role": "cook",
                        "scene_type": "emotion_to_practical",
                        "difficulty": "medium",
                        "input": f"cook {index}",
                        "target_behavior": ["target"],
                        "avoid_behavior": ["avoid"],
                        "tags": [],
                        "rubric_ref": "context",
                        "source_path": "demo/test.yaml",
                        "review_status": "candidate",
                        "conversation_id": f"cook-{index}",
                    }
                )
            records.append(
                {
                    "id": "dreamer_0",
                    "layer": "context_drift",
                    "role": "dreamer",
                    "scene_type": "emotion_to_practical",
                    "difficulty": "medium",
                    "input": "dreamer",
                    "target_behavior": ["target"],
                    "avoid_behavior": ["avoid"],
                    "tags": [],
                    "rubric_ref": "context",
                    "source_path": "demo/test.yaml",
                    "review_status": "candidate",
                    "conversation_id": "dreamer-0",
                }
            )
            write_json(
                dataset,
                {
                    "version": "v1",
                    "project": "demo",
                    "dataset_type": "character_prompt_eval",
                    "records": records,
                },
            )

            result = run_script(
                "select_hl_pilot_candidates.py",
                str(dataset),
                str(output),
                "--role",
                "cook",
                "--role",
                "dreamer",
                "--max-records",
                "2",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual([record["role"] for record in payload["records"]], ["cook", "dreamer"])

    def test_validate_failure_patterns_accepts_valid_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "demo.v1.json",
                {
                    "id": "demo.v1",
                    "role": "demo",
                    "scope": "project_extension",
                    "failure_modes": [
                        {
                            "id": "template_drift",
                            "description": "Role falls into a generic template.",
                            "signals": ["generic comfort", "ignores user wording"],
                            "linked_records": ["demo_001"],
                            "evidence": [{"kind": "human_review", "summary": "Observed in review."}],
                        }
                    ],
                },
            )
            (root / "README.md").write_text("# ignored\n", encoding="utf-8")

            result = run_script("validate_failure_patterns.py", str(root))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Validated 1 failure pattern files", result.stdout)

    def test_validate_failure_patterns_rejects_missing_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "bad.v1.json",
                {
                    "id": "bad.v1",
                    "role": "demo",
                    "scope": "project_extension",
                    "failure_modes": [
                        {
                            "id": "missing_signals",
                            "description": "No signals here.",
                            "evidence": [{"kind": "human_review", "summary": "Observed."}],
                        }
                    ],
                },
            )

            result = run_script("validate_failure_patterns.py", str(root))

            self.assertEqual(result.returncode, 1)
            self.assertIn("failure_modes[0].signals", result.stdout)

    def test_validate_hl_pilot_outputs_accepts_valid_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = root / "batch.review_batch.json"
            slice_path = root / "slice.v1.json"
            events = root / "events.jsonl"
            write_json(
                batch,
                {
                    "source_dataset": "demo.json",
                    "selection": {"roles": ["demo"], "max_records": 1},
                    "records": [{"id": "demo_001", "input": "hello"}],
                },
            )
            write_json(
                slice_path,
                {
                    "records": [
                        {
                            "id": "core_001",
                            "input": "hello",
                            "source_path": "demo.json",
                            "generic_dimension": "emotional_reception",
                        }
                    ]
                },
            )
            events.write_text(
                json.dumps(
                    {
                        "event_id": "evt_1",
                        "event_type": "experiment_started",
                        "dataset_path": str(batch),
                        "decision": {"reason": "valid"},
                        "evidence": {"kind": "human_review", "summary": "valid"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_script(
                "validate_hl_pilot_outputs.py",
                "--review-batch",
                str(batch),
                "--candidate-slice",
                str(slice_path),
                "--events",
                str(events),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("HL pilot outputs validated", result.stdout)

    def test_validate_hl_pilot_outputs_rejects_bad_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text("{not json}\n", encoding="utf-8")

            result = run_script("validate_hl_pilot_outputs.py", "--events", str(events))

            self.assertEqual(result.returncode, 1)
            self.assertIn("invalid JSONL", result.stdout)

    def test_validate_hl_pilot_outputs_rejects_slice_without_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slice_path = Path(tmp) / "slice.v1.json"
            write_json(
                slice_path,
                {
                    "records": [
                        {
                            "id": "core_001",
                            "input": "hello",
                            "generic_dimension": "emotional_reception",
                        }
                    ]
                },
            )

            result = run_script("validate_hl_pilot_outputs.py", "--candidate-slice", str(slice_path))

            self.assertEqual(result.returncode, 1)
            self.assertIn("source_path or source_id", result.stdout)

    def test_validate_hl_learning_state_accepts_valid_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "learning_state.v1.json"
            write_json(
                state,
                {
                    "system_id": "heuristic_eval_dataset_system",
                    "version": "v1",
                    "updated_at": "2026-05-19",
                    "active_loop": "hl_pilot",
                    "core_dimensions": [
                        {
                            "id": "emotional_reception",
                            "status": "candidate_evidence",
                            "evidence": ["case_001"],
                        }
                    ],
                    "memory_layers": {"event_log": "events.jsonl"},
                    "known_failure_patterns": [],
                    "open_gaps": ["needs replay"],
                    "reward_weights": {
                        "user_facing_relevance": 0.25,
                        "diagnostic_clarity": 0.2,
                        "cross_project_generality": 0.2,
                        "replay_stability": 0.15,
                        "noise_reduction": 0.1,
                        "compression_value": 0.1,
                    },
                    "allowed_actions": ["create_replay_batch"],
                    "blocked_actions": ["promote_to_accepted_without_replay"],
                    "next_replay_targets": ["promptfoo outputs"],
                },
            )

            result = run_script("validate_hl_learning_state.py", str(state))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("HL learning state validated", result.stdout)

    def test_validate_hl_learning_state_rejects_missing_reward_weight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "learning_state.v1.json"
            write_json(
                state,
                {
                    "system_id": "heuristic_eval_dataset_system",
                    "version": "v1",
                    "updated_at": "2026-05-19",
                    "active_loop": "hl_pilot",
                    "core_dimensions": [],
                    "memory_layers": {},
                    "known_failure_patterns": [],
                    "open_gaps": [],
                    "reward_weights": {"user_facing_relevance": 1.0},
                    "allowed_actions": [],
                    "blocked_actions": [],
                    "next_replay_targets": [],
                },
            )

            result = run_script("validate_hl_learning_state.py", str(state))

            self.assertEqual(result.returncode, 1)
            self.assertIn("reward_weights.diagnostic_clarity", result.stdout)

    def test_import_legacy_learning_bootstraps_manifest_and_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "legacy"
            output_dir = root / "bootstrap"
            (legacy / "role_eval" / "testsets" / "canonical").mkdir(parents=True)
            (legacy / "role_eval" / "testsets" / "results" / "full30").mkdir(parents=True)
            (legacy / "tapdoki" / "experiments").mkdir(parents=True)
            write_json(
                legacy / "role_eval" / "testsets" / "canonical" / "old_tests.json",
                {"records": []},
            )
            write_json(
                legacy / "role_eval" / "testsets" / "results" / "full30" / "results.json",
                {"results": []},
            )
            (legacy / "tapdoki" / "experiments" / "eval_summary.md").write_text(
                "# Summary\nRepeated stiffness under simple requests.\n",
                encoding="utf-8",
            )

            result = run_script(
                "import_legacy_learning.py",
                str(legacy),
                "--output-dir",
                str(output_dir),
                "--project",
                "demo",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
            state = json.loads((output_dir / "learning_state.v1.json").read_text(encoding="utf-8"))
            decision = json.loads((output_dir / "decision.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["import_type"], "legacy_learning_bootstrap")
            self.assertTrue(manifest["rules"]["legacy_import_is_not_accepted"])
            self.assertEqual(manifest["asset_counts"]["legacy_canonical_json"], 1)
            self.assertEqual(manifest["asset_counts"]["legacy_eval_result"], 1)
            self.assertEqual(manifest["asset_counts"]["legacy_summary"], 1)
            self.assertEqual(state["active_loop"], "legacy_import_bootstrap")
            self.assertIn("mutate_prompt_from_legacy_import_only", state["blocked_actions"])
            self.assertEqual(decision["primary_outcome"], "needs_human_review")

    def test_normalize_legacy_canonical_adds_traceability_and_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "character_eval_dataset.v1.json"
            output = Path(tmp) / "candidate.json"
            write_json(
                source,
                {
                    "version": "v1",
                    "project": "tapdoki",
                    "dataset_type": "character_prompt_eval",
                    "records": [
                        {
                            "id": "star_001",
                            "role": "star",
                            "review_status": "accepted",
                            "input": "hello",
                        }
                    ],
                },
            )

            result = run_script(
                "normalize_legacy_canonical.py",
                str(source),
                str(output),
                "--project",
                "demo",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            record = payload["records"][0]
            self.assertEqual(record["review_status"], "candidate")
            self.assertEqual(record["source_path"], str(source))
            self.assertEqual(record["source_index"], 0)
            self.assertEqual(record["source_id"], "star_001")
            self.assertTrue(payload["import_boundary"]["legacy_import_is_not_accepted"])

    def test_normalize_promptfoo_results_and_failure_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result_path = root / "promptfoo.json"
            summary_path = root / "failures.json"
            output = root / "observations.json"
            write_json(
                result_path,
                {
                    "results": {
                        "results": [
                            {
                                "success": True,
                                "score": 0.9,
                                "vars": {"question": "hi"},
                                "metadata": {
                                    "id": "case_001",
                                    "role": "star",
                                    "scene_type": "greeting",
                                    "prompt_variant": "compact",
                                },
                                "response": {"output": "hello"},
                                "gradingResult": {"reason": "pass"},
                            }
                        ]
                    }
                },
            )
            write_json(
                summary_path,
                [
                    {
                        "id": "case_002",
                        "role": "star",
                        "scene": "message_reply",
                        "question": "reply",
                        "output": "bad",
                        "reason": "too stiff",
                    }
                ],
            )

            result = run_script(
                "normalize_promptfoo_results.py",
                str(result_path),
                str(summary_path),
                "--output",
                str(output),
                "--project",
                "demo",
                "--run-id",
                "run_001",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["total"], 2)
            self.assertEqual(payload["summary"]["successes"], 1)
            self.assertEqual(payload["summary"]["failures"], 1)
            self.assertEqual(payload["observations"][0]["record_id"], "case_001")
            self.assertEqual(payload["observations"][1]["scene_type"], "message_reply")

    def test_run_hl_replay_dry_run_writes_observations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = root / "batch.json"
            context = root / "context.yaml"
            config = root / "config.yaml"
            output = root / "observations.json"
            write_json(
                batch,
                {
                    "records": [
                        {
                            "id": "core_001",
                            "source_record_id": "source_001",
                            "role": "demo",
                            "project": "demo",
                            "generic_dimension": "lightweight_practical_help",
                            "input": "Give me one small step.",
                            "target_behavior": ["one step"],
                            "avoid_behavior": ["long plan"],
                        }
                    ]
                },
            )
            context.write_text(
                """
version: v1
variables:
  series_core:
    value: Demo series.
prompt:
  system_template: |
    {{series_core}}
    {{character_context}}
  user_template: |
    {{input}}
""".strip(),
                encoding="utf-8",
            )
            config.write_text(
                f"""
version: v1
run_id: test_dry_run
input_path: {batch}
output_path: {output}
context_path: {context}
provider:
  type: openai_compatible
  model: demo-model
  api_key_env: MISSING_TEST_API_KEY
judge:
  enabled: false
""".strip(),
                encoding="utf-8",
            )

            result = run_script("run_hl_replay.py", str(config), "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["records"][0]["record_id"], "core_001")
            self.assertEqual(payload["records"][0]["source_record_id"], "source_001")
            self.assertEqual(payload["records"][0]["output"], "[DRY RUN]")
            self.assertIn("Demo series.", payload["records"][0]["rendered_messages"][0]["content"])

    def test_run_hl_replay_requires_api_key_for_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = root / "batch.json"
            context = root / "context.yaml"
            config = root / "config.yaml"
            output = root / "observations.json"
            write_json(batch, {"records": [{"id": "core_001", "input": "hello"}]})
            context.write_text(
                "version: v1\nprompt:\n  system_template: ''\n  user_template: '{{input}}'\n",
                encoding="utf-8",
            )
            config.write_text(
                f"""
version: v1
run_id: test_missing_env
input_path: {batch}
output_path: {output}
context_path: {context}
provider:
  type: openai_compatible
  model: demo-model
  api_key_env: MISSING_TEST_API_KEY
judge:
  enabled: false
""".strip(),
                encoding="utf-8",
            )

            result = run_script("run_hl_replay.py", str(config))

            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING_TEST_API_KEY", result.stdout)

    def test_run_hl_replay_dry_run_supports_enabled_judge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = root / "batch.json"
            context = root / "context.yaml"
            config = root / "config.yaml"
            output = root / "observations.json"
            write_json(
                batch,
                {
                    "records": [
                        {
                            "id": "core_001",
                            "input": "hello",
                            "target_behavior": ["brief greeting"],
                            "avoid_behavior": ["long lecture"],
                        }
                    ]
                },
            )
            context.write_text(
                "version: v1\nprompt:\n  user_template: '{{input}}'\n",
                encoding="utf-8",
            )
            config.write_text(
                f"""
version: v1
run_id: test_judge_dry_run
input_path: {batch}
output_path: {output}
context_path: {context}
provider:
  type: openai_compatible
  model: demo-model
  api_key_env: MISSING_TEST_API_KEY
judge:
  enabled: true
""".strip(),
                encoding="utf-8",
            )

            result = run_script("run_hl_replay.py", str(config), "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(payload["records"][0]["judge"]["enabled"])
            self.assertEqual(payload["records"][0]["judge"]["reason"], "dry run")

    def test_validate_hl_observations_accepts_valid_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            observations = Path(tmp) / "observations.json"
            write_json(
                observations,
                {
                    "version": "v1",
                    "run_id": "demo",
                    "input_path": "batch.json",
                    "context_path": "context.yaml",
                    "dry_run": True,
                    "records": [
                        {
                            "record_id": "core_001",
                            "input": "hello",
                            "output": "[DRY RUN]",
                            "judge": {"enabled": False},
                            "metadata": {"role": "demo"},
                            "failure_tags": [],
                        }
                    ],
                },
            )

            result = run_script("validate_hl_observations.py", str(observations))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Validated 1 observations", result.stdout)

    def test_validate_hl_observations_rejects_missing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            observations = Path(tmp) / "observations.json"
            write_json(
                observations,
                {
                    "version": "v1",
                    "run_id": "demo",
                    "records": [
                        {
                            "record_id": "core_001",
                            "input": "hello",
                            "judge": {"enabled": False},
                            "metadata": {"role": "demo"},
                            "failure_tags": [],
                        }
                    ],
                },
            )

            result = run_script("validate_hl_observations.py", str(observations))

            self.assertEqual(result.returncode, 1)
            self.assertIn("records[0].output", result.stdout)

    def test_validate_hl_dataset_candidate_units_accepts_valid_unit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            unit = Path(tmp) / "unit.json"
            write_json(
                unit,
                {
                    "unit_id": "tapdoki_dreamer_exact_help_001",
                    "version": "v1",
                    "trigger": {
                        "type": "human_review",
                        "summary": "Dreamer becomes poetic before completing exact-help requests.",
                    },
                    "diagnosis": "both_generic_and_role_specific",
                    "dataset_intent": "Build records that check whether the role completes exact small help before adding flavor.",
                    "candidate_destination": ["conversation_core_candidate", "project_failure_pattern"],
                    "reward_expectation": ["diagnostic_clarity", "noise_reduction"],
                    "replay_requirements": ["same role", "nearby exact-help scenes"],
                    "records": [
                        {
                            "id": "tapdoki_dreamer_exact_help_candidate_001",
                            "layer": "tiny_practical",
                            "role": "dreamer",
                            "scene_type": "message_reply",
                            "difficulty": "medium",
                            "input": "帮我回一句“我今天有点累，晚点再说”，不要解释。",
                            "target_behavior": ["provide one directly usable reply"],
                            "avoid_behavior": ["poetic atmosphere without usable reply"],
                            "tags": ["exact_help"],
                            "rubric_ref": "lightweight_practical_help",
                            "source_path": "eval_datasets/experiments/hl_pilot/dataset_candidate_units/unit.json",
                            "review_status": "candidate",
                        }
                    ],
                },
            )

            result = run_script("validate_hl_dataset_candidate_units.py", str(unit))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Validated 1 dataset candidate units", result.stdout)

    def test_validate_hl_dataset_candidate_units_rejects_missing_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            unit = Path(tmp) / "unit.json"
            write_json(
                unit,
                {
                    "unit_id": "bad_unit",
                    "version": "v1",
                    "trigger": {"type": "human_review", "summary": "Observed."},
                    "diagnosis": "case_issue",
                    "candidate_destination": ["experiment"],
                    "reward_expectation": ["diagnostic_clarity"],
                    "replay_requirements": ["same role"],
                    "records": [],
                },
            )

            result = run_script("validate_hl_dataset_candidate_units.py", str(unit))

            self.assertEqual(result.returncode, 1)
            self.assertIn("dataset_intent", result.stdout)

    def test_score_hl_mutation_writes_reward_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observations = root / "observations.json"
            output = root / "reward.json"
            write_json(
                observations,
                {
                    "version": "v1",
                    "run_id": "demo_run",
                    "records": [
                        {
                            "record_id": "core_001",
                            "input": "Give one small step.",
                            "output": "Put one shoe next to your foot.",
                            "judge": {"enabled": True, "pass": True, "score": 0.9, "reason": "Usable and brief."},
                            "metadata": {
                                "role": "slowpoke",
                                "generic_dimension": "lightweight_practical_help",
                            },
                            "failure_tags": [],
                        },
                        {
                            "record_id": "core_002",
                            "input": "Reply in one sentence.",
                            "output": "A poetic but unusable reply.",
                            "judge": {"enabled": True, "pass": False, "score": 0.3, "reason": "No usable sentence."},
                            "metadata": {
                                "role": "dreamer",
                                "generic_dimension": "lightweight_practical_help",
                            },
                            "failure_tags": ["task_completion_miss"],
                        },
                    ],
                },
            )

            result = run_script(
                "score_hl_mutation.py",
                str(observations),
                str(output),
                "--mutation-id",
                "demo_mutation",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["mutation_id"], "demo_mutation")
            self.assertIn(payload["decision"], {"keep_experiment", "needs_revision", "compress_candidate"})
            self.assertIn("diagnostic_clarity", payload["scores"])
            self.assertEqual(payload["hard_gates"]["has_replay"], True)

    def test_score_hl_mutation_rejects_empty_observations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            observations = Path(tmp) / "observations.json"
            output = Path(tmp) / "reward.json"
            write_json(observations, {"version": "v1", "run_id": "empty", "records": []})

            result = run_script("score_hl_mutation.py", str(observations), str(output))

            self.assertEqual(result.returncode, 1)
            self.assertIn("records must be a non-empty list", result.stdout)


if __name__ == "__main__":
    unittest.main()
