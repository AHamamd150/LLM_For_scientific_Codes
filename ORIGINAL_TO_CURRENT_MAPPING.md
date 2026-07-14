# 元の CoLLM ソースと現行パッケージの対応関係

作成日: 2026-06-19  
domain separation prototype 更新: 2026-06-20

## 1. この文書の目的

この文書は、元の `source.zip` に含まれていた CoLLM 実装と、整理・復元後の
`agentic-code-workbench` の対応関係を示す。

現行パッケージでは、元の一つのファイルに混在していた責務を、再利用可能な
package、汎用 code-generation backend、LHCO domain、workflow に分割している。
したがって、多くの項目は一対一のファイル移動ではなく、一つの元ファイルから
複数の現行ファイルへの分割となっている。

この対応表で使用する区分は次のとおり。

- **移設**: 主な実装を別のファイルへ移したもの
- **分割**: 一つの元ファイルの責務を複数ファイルへ分けたもの
- **置換**: 同じ目的を新しい interface／実装で置き換えたもの
- **統合**: workflow や共通 component に組み込んだもの
- **除外**: 現行の共有パッケージの対象外としたもの
- **新規**: 元の CoLLM にはなく、整理時に追加したもの

## 2. 全体対応

| 元のファイル／ディレクトリ | 現行の主な配置 | 区分 | 備考 |
| --- | --- | --- | --- |
| `source/LLM/collm_lhco.py` | `backends/code-generator/src/code_generator/` と `domains/lhco-domain/src/lhco_domain/` | 分割 | generic generation と LHCO card／prompt を分離 |
| `source/configs/system_prompt.txt` | `domains/lhco-domain/src/lhco_domain/prompts/codegen_system.txt` | 移設 | 内容は byte-for-byte で一致 |
| `source/configs/system_prompt.md` | 対応なし | 除外 | 現行生成で使用していた canonical prompt は `.txt` 版 |
| `source/LLM/pyfixer.py` | `backends/code-generator/src/code_generator/fixer.py` | 分割・置換 | prompt assembly と provider 呼び出しを分離。model loading は provider 側へ移動 |
| `source/runs/run_preselection.py` | `workflows/src/codegen_workflows/pipeline.py` | 分割・統合 | generate、execute、fix、regenerate の orchestration を workflow に移設 |
| `source/runs/run_preselection_GUI.py` | `workflows/src/codegen_workflows/pipeline.py`、`cli.py` | 置換 | GUI 用 entry point は廃止し、共通 workflow と CLI に統合 |
| `source/utils/read_configs.py` の `read_conf()` | `workflows/src/codegen_workflows/cli.py` | 置換 | YAML 一括設定から CLI argument へ変更 |
| `source/utils/read_configs.py` の DL 設定部分 | 対応なし | 除外 | MLP／GNN／Transformer とともに共有 workflow の対象外 |
| `source/utils/requirements_check.py` | 各 package の `pyproject.toml` | 置換 | import 時の自動 install を廃止し、依存関係を package metadata で宣言 |
| `source/utils/plot_checker.py` | 対応なし | 除外 | plot 数確認と watermark は初期の共有 package には含めていない |
| `source/utils/run_checker.py` | 対応なし | 除外 | 現行 workflow では使用していない |
| `source/GUI/` | 対応なし | 除外 | Streamlit GUI は共有 code-generation workflow の対象外 |
| `source/DL/MLP/` | 対応なし | 除外 | 独立した深層学習 application |
| `source/DL/GNN/` | 対応なし | 除外 | 独立した深層学習 application |
| `source/DL/Transformer/` | 対応なし | 除外 | 独立した深層学習 application |
| `source/LLM/old/` | 対応なし | 除外 | obsolete／failed／historical variants |
| `source/configs/old/` | 対応なし | 除外 | canonical でない過去の system prompt |

## 3. `source/LLM/collm_lhco.py` の詳細対応

| 元の要素 | 現行の要素 | 備考 |
| --- | --- | --- |
| `Config.SYSTEM_PROMPT_PATH` | `lhco_domain.profile.load_codegen_system_prompt()` | package data として prompt をロード |
| `Config.MAX_NEW_TOKENS` | `HuggingFaceCodeProvider(..., max_tokens=...)` と CLI の `--generator-max-tokens` | provider／実行時設定へ移動 |
| `Config.TEMPERATURE` | provider と `--generator-temperature` | 同上 |
| `Config.TOP_P`、`TOP_K`、`DO_SAMPLE` | 明示的な対応なし | 現行 provider interface では公開していない |
| `validate_python_syntax()` | `code_generator.python_validation.validate_python_syntax()` | 移設 |
| `ensure_packages()` | 各 `pyproject.toml` | import 時の package install は廃止 |
| `load_text_file()` | `lhco_domain.profile.load_codegen_system_prompt()` | system prompt 専用 loader に縮小 |
| `extract_python_code()` | `code_generator.model_response.extract_python_code()` | 移設 |
| `clean_think_blocks()` | `code_generator.model_response.clean_think_blocks()` | 移設 |
| `save_text()`、`save_code()` | `codegen_workflows.pipeline.ResearchCodeWorkflow` の artifact 書き出し | workflow が保存先を所有 |
| `looks_incomplete_python()` | `code_generator.model_response.looks_incomplete_python()` | continuation 判定として移設 |
| `parse_user_input()`、`parse_user_input_text()` | `lhco_domain.cards.parse_card()` | path と text の二系統を text parser に統一 |
| `get_device_and_dtype()` | provider implementation | generator core から device 管理を除去 |
| `load_model_and_tokenizer()` | `code_generator.providers.huggingface.HuggingFaceCodeProvider` | model/API access を adapter 化 |
| `build_continue_prompt()` | `code_generator.generator.CONTINUE_PROMPT` と `CodeGenerator.generate()` | message list を直接継続 |
| `build_prompt()` | `lhco_domain.profile.LHCOGenerationProfile.build_messages()` | system/user message を構築 |
| `generate_code()` | `code_generator.generator.CodeGenerator.generate()` | local／API 共通の生成 orchestration |
| `generate_code_api()` | `HuggingFaceCodeProvider.complete()` + `CodeGenerator.generate()` | API 固有処理を provider に分離 |
| `generate_lhco_code()` | `CodeGenerator.generate()` + workflow／CLI | 生成、保存、provider 構築を分離 |
| `generate_lhco_code_legacy()` | 対応なし | 元 signature の compatibility wrapper は公開していない |

### 3.1 continuation

元実装と現行実装はいずれも、一度の generation につき continuation は最大1回である。

現行配置:

- 未完了判定: `code_generator/model_response.py`
- continuation 指示: `code_generator/generator.py`
- model 再呼び出し: `code_generator/generator.py`
- code part の結合: `code_generator/model_response.py`

現行の `merge_code_parts()` では、元の単純連結に加えて、重複行の除去と
末尾が `:` の場合の indentation 補正を行う。

## 4. `source/LLM/pyfixer.py` の詳細対応

| 元の要素 | 現行の要素 | 備考 |
| --- | --- | --- |
| `SYSTEM_PROMPT` | `code_generator.fixer.FIX_SYSTEM_PROMPT` | 簡潔化した generic Python repair prompt |
| `clean_think_blocks()` | `code_generator.model_response.clean_think_blocks()` | generator と共用 |
| `_get_device_and_dtype()`、`_load_model()` | `code_generator.providers.*` | model/device 管理を provider へ移動 |
| `_extract_code()` | `code_generator.model_response.extract_python_code()` | generator と共用 |
| `_parse_error()` | 明示的な対応なし | 現行では full traceback を直接 prompt に渡す |
| `_validate_syntax()` | `code_generator.python_validation.validate_python_syntax()` | utility は存在するが、fixer 内では直接使用していない |
| `_add_line_numbers()` | `code_generator.fixer.build_fix_messages()` 内 | 内部処理として保持 |
| `_build_fix_messages()` | `code_generator.fixer.build_fix_messages()` | 移設・簡潔化 |
| `_fix_code_api()` | provider の `complete()` | provider interface に統合 |
| `fix_code()` | `code_generator.fixer.fix_code()` | model ID ではなく provider を受け取る |

`fixer.py` 自体は LHCO 固有処理を含まず、Python code と traceback を入力とする。
ただし現時点では package 配置は `code-generator` 内である。

## 5. `source/runs/run_preselection.py` の詳細対応

| 元の要素 | 現行の要素 | 備考 |
| --- | --- | --- |
| `recreate_dir()` | `RunLayout.create()` | 現行では run directory を削除せず必要な subdirectory を作成 |
| `snapshot_file()` | workflow 内の attempt artifact 保存 | 各候補 code を個別ファイルへ保存 |
| `extract_python_from_fix_response()` | `extract_python_code()` と `fix_code()` | fixer 応答の抽出時に正規化 |
| `run_and_capture_error()` | `code_generator.executor.execute_python()` | subprocess 実行を独立 utility 化 |
| `run_LLM()` | `ResearchCodeWorkflow.generate_and_review()` | helper selection、generation、execution、critique を構成 |
| `MAX_RETRIES` | `max_retries`、CLI `--max-retries` | 既定値3。旧 `--max-fix-attempts` は alias として維持 |
| YAML `DEFAULT_MODEL` | module ごとの CLI model option | helper、generator、fixer、tracer、critique を個別指定可能 |
| YAML `Input_file` | CLI `--input` | optional execution input passed to generated code as `sys.argv[1]` |
| YAML `User_input` | CLI `--card` | card path |
| YAML `Use_api`、API key | provider adapter／環境変数 | credential を workflow から分離 |

### 5.1 復元済みの実行回復ループ

元実装の `MAX_RETRIES` は単なる fix 回数ではなく、各 trial で次を行う。

```text
initial generation
    → execute
    → failure
        → fix
        → execute
        → failure
            → regenerate from the generation card
            → execute
            → failure
                → next trial
```

この処理は現在、
`workflows/src/codegen_workflows/pipeline.py` の
`_execute_fix_and_regenerate()` に復元されている。

`max_retries = N` の最大実行回数は次のとおり。

```text
1 initial execution + N fix executions + N regeneration executions
= 1 + 2N
```

たとえば `max_retries=2` では最大5回実行し、artifact は次のようになる。

```text
execution/
├── generated_analysis.py
├── cutflow.txt
└── generation_info/
    ├── attempt_001_initial_stderr.txt
    ├── attempt_002_fix_stderr_trial_1.txt
    ├── attempt_003_regen_stderr_trial_1.txt
    ├── attempt_004_fix_stderr_trial_2.txt
    └── attempt_005_regen_stderr_trial_2.txt
```

次の trial の fixer 入力は、直前に失敗した fix candidate ではなく、
直前に全再生成した code である。この点も元の処理と一致する。

## 6. system prompt と helper registry

### 6.1 system prompt

| 元の配置 | 現行配置 | 状態 |
| --- | --- | --- |
| `source/configs/system_prompt.txt` | `domains/lhco-domain/src/lhco_domain/prompts/codegen_system.txt` | byte-for-byte で一致 |

prompt は LHCO 固有であるため、generic `code-generator` から
`lhco-domain` package へ移した。内容は変更していない。

### 6.2 helper registry

元の `source.zip` には、現在の形式の独立した helper registry package は含まれていない。
helper function の実装は主として system prompt 内に記載されていた。

現行では、helper の選択用 metadata を次へ分離している。

```text
domains/lhco-domain/src/lhco_domain/registry.py
domains/lhco-domain/src/lhco_domain/prompts/helper_policy.txt
```

実装本体は引き続き `codegen_system.txt` 内にあり、registry は helper 名、
用途、keyword、alias、dependency を selector と Oracle に提供する。

## 7. 元ソースにはなく、現行で追加された component

| 現行 component | 役割 |
| --- | --- |
| `packages/helper-selector/` | closed registry から helper を選択し、dependency を展開 |
| `domains/lhco-domain/` | LHCO／CoLLM prompts、helper metadata、selection policy、Oracle/Critique context |
| `packages/golden-axe-oracle/` | code generation 前の仕様曖昧性検査。canonical Oracle／Oraclet と split profile を保持 |
| `packages/critique-pipeline/` | tracer による実装抽出と semantic critique |
| `packages/workbench-contracts/` | run layout、artifact、protocol の共通定義 |
| `workflows/` | accepted card 以降の component 順序、artifact 保存、execution recovery を管理 |
| `examples/cases/` | original task card の例 |
| `examples/reference/helper-selected/` | helper selection 後の card の参照例 |

## 8. 現在の処理フロー

```text
input card
   |
   +--> standalone Golden Axe Oracle
           |
           +--> human clarification / accepted card
                   |
                   +--> Helper Selector
           |
           +--> generation card with [ADDITIONAL_HELPERS]
                   |
                   +--> CodeGenerator
                           |
                           +--> optional one-pass continuation
                           |
                           +--> generated Python
                                   |
                                   +--> optional LHCO execution
                                   |       |
                                   |       +--> fix
                                   |       +--> regenerate
                                   |       +--> repeat up to max_retries
                                   |
                                   +--> tracer
                                           |
                                           +--> critique
```

## 9. 除外したコードの扱い

次のコードは削除対象というより、共有 code-generation package の対象外として
現行アーカイブに含めていない。

- Streamlit GUI
- MLP／GNN／Transformer application
- plot checker と watermark
- package の自動 install／端末環境診断
- historical system prompt
- old LLM／fixer variants

必要であれば元の `source.zip` から独立 package または application として再整理できる。
ただし、現在の standalone Oracle と、accepted card 以降の
helper selection → generation → execution recovery → critique には依存しない。

## 10. 対応確認時の注意

1. `collm_lhco.py` は現行では一つのファイルに対応しない。主に
   `lhco_domain/cards.py`、`lhco_domain/profile.py`、
   `code_generator/generator.py`、`code_generator/model_response.py`、
   `code_generator/python_validation.py`、`providers/` に分割されている。
2. 元の `run_preselection.py` の retry は、fix retry ではなく
   **fix＋全再生成の trial** である。
3. generation 内 continuation と execution failure recovery は別の機構である。
4. system prompt は byte-for-byte で保持され、LHCO domain package にある。
5. GUI／DL code は、共有パッケージから除外しただけで、現行 component へ移植した
   わけではない。
