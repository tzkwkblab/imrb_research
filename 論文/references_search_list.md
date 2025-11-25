# 参考文献調査用チェックリスト

このファイルは、論文で使用する参考文献28件を **一つずつ漏れなく確認するための進捗管理用リスト** です。

- `Status` は次のいずれかを使います: `TODO` / `CHECKING` / `DONE` / `NEED_FIX` / `DUPLICATE`
- 各行の `Notes` に、修正方針や確認メモを1行で簡潔に書きます。

## 各文献の調査チェックリスト

1. **存在確認**: 調査用キーワードを Google Scholar / arXiv / 出版社サイトで検索し、該当論文が存在するか確認する。
2. **メタ情報確認**: タイトル、筆頭著者名、出版年、会議/ジャーナル名（または arXiv ID）を確認する。
3. **安定リンク取得**: DOI、arXiv ID、公式ページURLなど、今後も変わりにくいリンクを1つメモする（必要なら `Notes` に簡潔に記載）。
4. **Bibキー対応確認**: `Bibキー` と実際の文献情報の対応関係（別名や略称がないか）を確認する。
5. **重複・紛らわしさ確認**: 類似タイトルや同名論文がないか軽く確認し、あれば `Notes` に区別のメモを書く。

各No.の調査が終わったら、その行の `Status` を `DONE` に更新し、修正が必要なら `NEED_FIX` として内容を `Notes` に書きます。

## No.8 / No.15 の重複候補の扱い

- No.8 (`xu2024concept`) と No.15 (`schrodi2024unsupervised`) は、どちらもタイトルが「Concept Bottleneck Models Without Predefined Concepts」です。
- 調査時は、必ず **両方のキーワード** で検索し、次を比較して同一論文かどうかを確認します。
  - 著者名（全員）
  - arXiv ID
  - タイトル

- **同一論文だった場合**
  - どちらを採用Bibキーとするか（例: `schrodi2024unsupervised`）を決め、採用側の行の `Notes` に「Bibキー統一: xxx に統一」と書く。
  - もう一方の行は `Status=DUPLICATE` とし、`Notes` に「xxx と同一論文（arXiv:YYYY.NNNNN）」のようにメモする。

- **別論文だった場合**
  - `Notes` に「別論文（著者や arXiv ID が異なる）」と簡潔に書き分ける。
  - 必要に応じて、将来Bibキーを見直す場合の候補（例: 著者ベースのキー名）も `Notes` に書いておく。

## 文献一覧と調査ステータス

| No. | Bibキー                                  | タイトル                                                     | 年   | 出典・種別（ざっくり）                                      | 調査用キーワード例                                                     | Status     | Notes |
|----:|------------------------------------------|--------------------------------------------------------------|------|------------------------------------------------------------|------------------------------------------------------------------------|------------|-------|
|  1  | pontiki-EtAl:2014:SemEval2014Task4       | SemEval-2014 Task 4: Aspect Based Sentiment Analysis         | 2014 | SemEval 2014 ワークショップ論文                            | "SemEval-2014 Task 4: Aspect Based Sentiment Analysis" Pontiki        | DONE       | references.tex と一致 (SemEval 2014) |
|  2  | ribeiro2016should                        | Why should I trust you?: Explaining the predictions of any classifier | 2016 | KDD 2016 会議論文                                           | "Why should I trust you?" Ribeiro 2016 KDD                            | DONE       | references.tex と一致 (KDD 2016) |
|  3  | lundberg2017unified                      | A unified approach to interpreting model predictions         | 2017 | NeurIPS (NIPS) 論文                                       | "A unified approach to interpreting model predictions" Lundberg       | DONE       | references.tex と一致 (NeurIPS, vol.30) |
|  4  | wachter2017counterfactual                | Counterfactual explanations without opening the black box: Automated decisions and the GDPR | 2017 | Harvard Journal of Law & Technology 論文                   | "Counterfactual explanations without opening the black box" Wachter   | DONE       | references.tex と一致 (Harvard JOLT 31(2)) |
|  5  | kim2018interpretability                  | Interpretability beyond feature attribution: Quantitative testing with concept activation vectors (TCAV) | 2018 | ICML 2018 会議論文                                         | "Interpretability beyond feature attribution" Kim TCAV                | DONE       | references.tex と一致 (ICML 2018, TCAV) |
|  6  | luss2024cell                             | CELL your Model: Contrastive Explanations for Large Language Models | 2024 | arXiv プレプリント                                         | "CELL your Model: Contrastive Explanations for Large Language Models" | DONE       | references.tex で arXiv:2406.11785 を確認 |
|  7  | bucinca2024contrastive                   | Contrastive Explanations That Anticipate Human Misconceptions Can Improve Human Decision-Making Skills | 2024 | arXiv プレプリント                                         | "Contrastive Explanations That Anticipate Human Misconceptions"       | DONE       | references.tex で arXiv:2410.04253 を確認 |
|  8  | xu2024concept                            | Concept Bottleneck Models Without Predefined Concepts       | 2024 | arXiv プレプリント                                         | "Concept Bottleneck Models Without Predefined Concepts" Xu            | DUPLICATE  | schrodi2024unsupervised と同一論文 (arXiv:2407.03921) |
|  9  | anthropic2025biology                     | On the Biology of a Large Language Model                    | 2025 | Transformer Circuits オンライン記事                       | "On the Biology of a Large Language Model" Anthropic                  | DONE       | references.tex の URL/タイトルを確認 |
| 10  | alghamdi2024dynamic                      | Dynamic Sentiment Analysis with Local Large Language Models using Majority Voting | 2024 | arXiv プレプリント                                         | "Dynamic Sentiment Analysis with Local Large Language Models"         | DONE       | references.tex で arXiv:2407.13069 を確認 |
| 11  | demszky2020goemotions                    | GoEmotions: A Dataset of Fine-Grained Emotions              | 2020 | ACL 2020 会議論文                                          | "GoEmotions: A Dataset of Fine-Grained Emotions" Demszky              | DONE       | references.tex と一致 (ACL 2020 GoEmotions) |
| 12  | srec:steam-review-aspect-dataset         | Steam review aspect dataset                                 | 2024 | Webデータセット記事（S. Khosasi, srec.ai）                | "Steam review aspect dataset" Khosasi                                 | DONE       | references.tex の URL を確認 (srec.ai) |
| 13  | papineni-etal-2002-bleu                  | BLEU: a Method for Automatic Evaluation of Machine Translation | 2002 | ACL 2002 会議論文                                          | "BLEU: a Method for Automatic Evaluation of Machine Translation"      | DONE       | references.tex と一致 (ACL 2002 BLEU) |
| 14  | devlin2018bert                           | BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding | 2018 | arXiv プレプリント                                         | "BERT: Pre-training of Deep Bidirectional Transformers" Devlin        | DONE       | references.tex で arXiv:1810.04805 を確認 |
| 15  | schrodi2024unsupervised                  | Concept Bottleneck Models Without Predefined Concepts       | 2024 | arXiv プレプリント（タイトルがNo.8と同一）                | "Concept Bottleneck Models Without Predefined Concepts" Schrodi       | DONE       | references.tex で arXiv:2407.03921 を確認; Bibキー統一候補 |
| 16  | ameisen2025attribution                   | Circuit Tracing: Revealing Computational Graphs in Language Models | 2025 | Transformer Circuits オンライン記事                       | "Circuit Tracing: Revealing Computational Graphs in Language Models"  | DONE       | references.tex の URL を確認 (Transformer Circuits, methods) |
| 17  | bordt2022posthoc                         | Post-Hoc Explanations Fail to Achieve their Purpose in Adversarial Contexts | 2022 | FAccT 2022 会議論文                                        | "Post-Hoc Explanations Fail to Achieve their Purpose" Bordt           | DONE       | references.tex と一致 (FAccT 2022) |
| 18  | kardale2023contrastive                   | Contrastive text summarization: a survey                    | 2023 | International Journal of Information and Computation 論文  | "Contrastive text summarization: a survey" Kardale                    | DONE       | references.tex と一致 (Int. J. Information and Computation) |
| 19  | saha2024strumllm                         | STRUM-LLM: Attributed and Structured Contrastive Summarization for User-Oriented Comparison | 2024 | arXiv プレプリント                                         | "STRUM-LLM: Attributed and Structured Contrastive Summarization"      | DONE       | references.tex で arXiv:2403.19710 を確認 |
| 20  | luo2024chatabsa                          | ChatABSA: A Novel Framework for Aspect-based Sentiment Analysis using Large Language Models | 2024 | arXiv プレプリント                                         | "ChatABSA: A Novel Framework for Aspect-based Sentiment Analysis"     | DONE       | references.tex で arXiv:2401.08226 を確認 |
| 21  | wang2024llmcluster                       | Improving Clustering Performance by Leveraging Large Language Models | 2024 | arXiv プレプリント                                         | "Improving Clustering Performance by Leveraging Large Language Models"| DONE       | references.tex で arXiv:2410.00927 を確認 |
| 22  | sellam-etal-2020-bleurt                  | BLEURT: Learning Robust Metrics for Text Generation         | 2020 | ACL 2020 会議論文                                          | "BLEURT: Learning Robust Metrics for Text Generation"                 | DONE       | references.tex と一致 (ACL 2020 BLEURT) |
| 23  | yuan2021bartscore                        | BARTScore: Evaluating Generated Text as Text Generation     | 2021 | NeurIPS 2021 論文                                          | "BARTScore: Evaluating Generated Text as Text Generation"             | DONE       | references.tex と一致 (NeurIPS 2021 BARTScore) |
| 24  | reiter2018structured                     | A Structured Review of the Validity of BLEU                 | 2018 | Computational Linguistics 誌                                | "A Structured Review of the Validity of BLEU" Reiter                  | DONE       | references.tex と一致 (Computational Linguistics 44(3)) |
| 25  | holtzman2020curious                      | The Curious Case of Neural Text Degeneration               | 2020 | ICLR 2020 論文                                             | "The Curious Case of Neural Text Degeneration" Holtzman               | DONE       | references.tex と一致 (ICLR 2020) |
| 26  | vaswani2017attention                     | Attention is All you Need                                   | 2017 | NeurIPS (NIPS) 2017 論文                                   | "Attention is All you Need" Vaswani                                   | DONE       | references.tex と一致 (NeurIPS 2017 Attention) |
| 27  | zhang2019bertscore                       | BERTScore: Evaluating Text Generation with BERT             | 2019 | arXiv プレプリント                                         | "BERTScore: Evaluating Text Generation with BERT"                     | DONE       | references.tex で arXiv:1904.09675 を確認 |
| 28  | stein2024towards                         | Towards Compositionality in Concept Learning                | 2024 | ICML 2024 会議論文                                         | "Towards Compositionality in Concept Learning" Stein                  | DONE       | references.tex と一致 (ICML 2024) |

## LaTeX参考文献との対応関係メモ

LaTeX 側の参考文献は `論文/chapters/references.tex` に直接 `thebibliography` 環境で書かれています。

- Bibキーは `\bibitem{...}` の中かっこ内と、この表の `Bibキー` 列が対応します。
- 次の2つの観点で対応関係をチェックします（必要に応じて下のリストを埋める想定です）。

- MarkdownにはあるがLaTeX側にないキー候補:
  - （必要になったらここに列挙）

- LaTeX側にはあるがMarkdownにないキー候補:
  - （必要になったらここに列挙）

LaTeX側の文献表記の修正方針メモ（例: タイトルの大文字小文字、会議名表記など）もここに箇条書きで追加して構いません。

## 最終確認フロー

- `Status` 列が `TODO` / `CHECKING` の行が **0件** になるまで確認を進める。
- 全行が `DONE` または `NEED_FIX` / `DUPLICATE` だけになっていることを、このファイル上で目視確認する。
- 必要な修正をLaTeX側（`references.tex` や他の `.tex`）に反映したあと、LaTeXをコンパイルして次を確認する:
  - 引用に `?` が残っていないこと
  - 参考文献リストに、必要な文献がすべて含まれていること（重複統合・削除後の最終件数で問題ないこと）
