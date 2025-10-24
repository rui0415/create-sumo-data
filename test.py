import pandas as pd

def count_diff_rows(file1_path, file2_path, decimal_places=8):
    """
    浮動小数点数の丸め誤差を無視して比較し、合計でいくつの異なる行があったかを出力します。
    """
    try:
        # 0. ファイルパスが同じかどうかチェック（実行例ではパスが異なっているため、意図しない比較を防ぐために追加）
        if file1_path == file2_path:
            print("🚨 警告: 比較対象のファイルパスが同じです。")
            return 0

        df1_orig = pd.read_csv(file1_path)
        df2_orig = pd.read_csv(file2_path)

        # 1. 形状チェック
        if df1_orig.shape != df2_orig.shape:
            print(f"❌ ファイルは異なります（形状が不一致: {df1_orig.shape} vs {df2_orig.shape}）。")
            return -1 # 不一致を示すために-1を返す

        # 2. 比較用のデータフレームを作成し、浮動小数点数を丸める
        df1 = df1_orig.copy()
        df2 = df2_orig.copy()

        float_cols = df1.select_dtypes(include=['float']).columns

        # 浮動小数点数を丸める
        if not float_cols.empty:
            df1[float_cols] = df1[float_cols].round(decimal_places)
            df2[float_cols] = df2[float_cols].round(decimal_places)

        # 3. 差異マスクを作成し、異なる行の合計を計算
        comparison_result = (df1 == df2)

        # 少なくとも一つの列が異なる行（行全体が一致しない行）を特定
        diff_rows_mask = ~comparison_result.all(axis=1)

        # 異なる行の合計数を取得
        diff_count = diff_rows_mask.sum()

        if diff_count == 0:
            print(f"\n🎉 比較の結果、丸め誤差（{decimal_places}桁）を無視すれば両ファイルは完全に一致しています。")
        else:
            print(f"\n❌ {diff_count} 行で差異が見つかりました。（丸め誤差 {decimal_places} 桁を無視）")

        return diff_count

    except FileNotFoundError:
        print("指定されたCSVファイルが見つかりません。")
        return -1
    except Exception as e:
        print(f"処理中に予期せぬエラーが発生しました: {e}")
        return -1

# 実行例（ファイルパスを修正し、丸め桁数を設定してください）
# 実行例のファイルパスが異なっているため、ここでは仮に修正して実行します
file_a = './csv/re-manhattan_seed256_n100.csv'
file_b = './re-manhattan_seed256_n100.csv'

total_diffs = count_diff_rows(
    file_a,
    file_b,
    decimal_places=8 # 小数点以下0桁で比較（整数値の比較に近い）
)

print(f"合計差異行数: {total_diffs}")
