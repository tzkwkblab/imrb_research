# Steam Few-shot実験結果レポート

生成日時: 2025-11-26 15:40:42

## 実行統計

- 総実験数: 12
- 成功: 12
- 失敗: 0

## Few-shot別統計

| Few-shot | 実験数 | 平均BERT | 最小BERT | 最大BERT | 平均BLEU | 最小BLEU | 最大BLEU |
|----------|--------|----------|----------|----------|----------|----------|----------|
| 0 | 4 | 0.5676 | 0.5200 | 0.6260 | N/A | N/A | N/A |
| 1 | 4 | 0.6438 | 0.5840 | 0.7175 | N/A | N/A | N/A |
| 3 | 4 | 0.6899 | 0.5647 | 0.7925 | 0.0102 | N/A | 0.0408 |

## Few-shot影響分析表

| アスペクト | 0-shot BERT | 1-shot BERT | 3-shot BERT | 0-shot BLEU | 1-shot BLEU | 3-shot BLEU |
|----------|-------------|-------------|-------------|-------------|-------------|-------------|
| audio | 0.5441 | 0.5840 | 0.5647 | 0.0000 | 0.0000 | 0.0000 |
| gameplay | 0.5804 | 0.6287 | 0.7925 | 0.0000 | 0.0000 | 0.0408 |
| story | 0.5200 | 0.7175 | 0.7676 | 0.0000 | 0.0000 | 0.0000 |
| visual | 0.6260 | 0.6449 | 0.6347 | 0.0000 | 0.0000 | 0.0000 |

## 詳細結果表

| 実験ID | アスペクト | Few-shot | BERT | BLEU | ステータス |
|--------|----------|----------|------|------|----------|
| steam_gameplay_0_4o-mini_word | gameplay | 0 | 0.5804 | 0.0000 | 成功 |
| steam_gameplay_1_4o-mini_word | gameplay | 1 | 0.6287 | 0.0000 | 成功 |
| steam_gameplay_3_4o-mini_word | gameplay | 3 | 0.7925 | 0.0408 | 成功 |
| steam_visual_0_4o-mini_word | visual | 0 | 0.6260 | 0.0000 | 成功 |
| steam_visual_1_4o-mini_word | visual | 1 | 0.6449 | 0.0000 | 成功 |
| steam_visual_3_4o-mini_word | visual | 3 | 0.6347 | 0.0000 | 成功 |
| steam_story_0_4o-mini_word | story | 0 | 0.5200 | 0.0000 | 成功 |
| steam_story_1_4o-mini_word | story | 1 | 0.7175 | 0.0000 | 成功 |
| steam_story_3_4o-mini_word | story | 3 | 0.7676 | 0.0000 | 成功 |
| steam_audio_0_4o-mini_word | audio | 0 | 0.5441 | 0.0000 | 成功 |
| steam_audio_1_4o-mini_word | audio | 1 | 0.5840 | 0.0000 | 成功 |
| steam_audio_3_4o-mini_word | audio | 3 | 0.5647 | 0.0000 | 成功 |
