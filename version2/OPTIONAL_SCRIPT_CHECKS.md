# 追加スクリプトの実行確認手順

## この手順の位置付け

通常の生成処理と Oracle 各入口の確認は完了している。ここでは追加機能だけを、既に得られた Case 1 の生成コードで確認する。全7ケースの再実行や、論文実験の再集計は不要である。API の応答が安定しているときに実行すればよい。

この手順書の作成時には、以下の API 実行は行っていない。

実行順序は次のとおり。

1. 既存コードに Tracer/Critique だけを32Bで再適用する。
2. 元の14B Tracer 出力を `evaluate_tracer.py` で評価する。
3. 新しい32B Tracer 出力を同じ評価モデルで評価する。

これは入口・入出力の動作確認であり、1件の結果からモデル性能を比較する実験ではない。

## 0. 準備

`collm-test` 環境を有効にし、`ver2` のルートへ移動する。以下はすべてパッケージルートから実行する。

主処理の確認に使った出力先を指定する。

```bash
CHECK_RUN=runs/clean_check_case1
```

別の出力先で成功した場合は、この変数だけ変更する。次の4ファイルが存在することを確認する。

```bash
ls "$CHECK_RUN/cards/accepted.txt" \
   "$CHECK_RUN/cards/generation.txt" \
   "$CHECK_RUN/execution/generated_analysis.py" \
   "$CHECK_RUN/critique/tracer/final_output.txt"
```

追加機能1には既に使用した `HF_TOKEN` が必要。追加機能2・3には OpenAI API の認証が必要になる。

```bash
python -m pip install openai
export OPENAI_API_KEY="your-key"
```

`evaluate_tracer.py` の既定モデルは `gpt-5.6-luna`。別のモデルを使う場合は `EVALUATION_MODEL` を設定する。スクリプトは Responses API と `reasoning.effort=low` を使うため、利用可能で、この指定に対応するモデルを選ぶ。既定モデルの現在の利用可否は本確認では未検証である。

## 1. Tracer/Critique だけを32Bで再実行

`run_qwen3_32b_postreview.sh` は `frozen_timing/` を固定参照する。その配置に合わせるために、今回の出力をコピーする必要はない。今回は同じ処理の CLI に入力パスを直接渡す。

```bash
PYTHONPATH=packages/critique-pipeline/src \
python -m critique_pipeline.cli run \
  --card "$CHECK_RUN/cards/generation.txt" \
  --code "$CHECK_RUN/execution/generated_analysis.py" \
  --tracer-model Qwen/Qwen3-32B \
  --critique-model Qwen/Qwen3-32B \
  --domain-context domains/lhco-domain/src/lhco_domain/prompts/critique_context.txt \
  --n-runs 1 --no-repair \
  --run-dir "$CHECK_RUN/postreview_32b_check"
```

Hugging Face API を使う。コード生成・解析実行はやり直さず、元の Tracer/Critique 出力も上書きしない。

成功後、次の出力があることを確認する。

```bash
ls "$CHECK_RUN/postreview_32b_check/tracer/final_output.txt" \
   "$CHECK_RUN/postreview_32b_check/critique/response_001.txt" \
   "$CHECK_RUN/postreview_32b_check/critique/filtered_review.txt"
```

単独の Critique CLI は結果を `critique/` に保存する。通常の主処理の `critique/findings/` とは配置が異なる。

### `run_qwen3_32b_postreview.sh` 自体を確認する場合

必要な入力が既に `frozen_timing/run_01/case1/execution/generated_analysis.py` にある場合だけ、次でも確認できる。上の CLI 実行と両方を必ず行う必要はない。

```bash
bash scripts/run_qwen3_32b_postreview.sh 1 1
```

この wrapper は Case 1 のカードを読み、`frozen_timing/run_01/case1/critique_qwen3_32b/` に保存する。既存出力先がある場合は停止する。過去の入力が `paper_data/` へ移動済みなら、wrapper 内の入力・出力先を確認してから使用する。保存済みの論文データをこの動作確認のために移動・削除する必要はない。

以下の手順3は、最初の直接 CLI で作った `postreview_32b_check/` を参照する。wrapper を使った場合は `--trace` を、その wrapper が作った `tracer/final_output.txt` へ変更する。

## 2. 元の14B Tracer 出力を評価

```bash
python scripts/evaluate_tracer.py \
  --case 1 --run 1 \
  --task-card "$CHECK_RUN/cards/accepted.txt" \
  --code "$CHECK_RUN/execution/generated_analysis.py" \
  --trace "$CHECK_RUN/critique/tracer/final_output.txt" \
  --model "${EVALUATION_MODEL:-gpt-5.6-luna}" \
  --out tracer_evaluation_check/case1_run01_trace14b.csv
```

OpenAI API を使う。入力カードは、その実行で保存した `accepted.txt` を用い、実行後に編集された可能性のある examples のカードとの取り違えを避ける。`--case` と `--run` は CSV に付ける識別情報である。

成功後、CSV にヘッダーと要求項目の評価行があることを確認する。

```bash
head -n 5 tracer_evaluation_check/case1_run01_trace14b.csv
```

## 3. 新しい32B Tracer 出力を評価

手順1の Tracer 出力を指定し、評価モデルは手順2と同じにする。

```bash
python scripts/evaluate_tracer.py \
  --case 1 --run 1 \
  --task-card "$CHECK_RUN/cards/accepted.txt" \
  --code "$CHECK_RUN/execution/generated_analysis.py" \
  --trace "$CHECK_RUN/postreview_32b_check/tracer/final_output.txt" \
  --model "${EVALUATION_MODEL:-gpt-5.6-luna}" \
  --out tracer_evaluation_check/case1_run01_trace32b.csv
```

```bash
head -n 5 tracer_evaluation_check/case1_run01_trace32b.csv
```

ここまでで、既存コードの再レビューと、Tracer 出力の評価を1件ずつ確認できる。評価 CSV はモデルによる判定であり、利用時には人が内容を確認する。

## 途中で API エラーになった場合

504 などの API エラーなら、その段階の確認は未完了として後日に回す。既存の解析コードや論文データを消して最初から生成し直す必要はない。手順1が完了しなくても、既存の14B Tracer 出力を使う手順2は独立に実行できる。

`scripts/oldscripts/` の一括評価用 wrapper は、この1件確認には不要である。
