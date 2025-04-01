import pandas as pd
from typing import List


class CSVInfo:
    def __init__(self, columns: List[str], dataframe: pd.DataFrame, path: str):
        self.COLUMNS = columns
        self.DATAFRAME = dataframe
        self.PATH = path
        self.stats_df = None  # 初始化共享变量
        self.info()  # 关键修改：实例化时自动生成统计结果

    def info(self) -> None:
        """生成统计信息并保存到 stats_df"""
        stats = []
        df = self.DATAFRAME
        columns = self.COLUMNS

        for col in columns:
            # 计算长度（排除空值）
            lengths = df[col].apply(lambda x: len(str(x)) if x != '' else 0)

            # 统计非空值数量
            empty = df[col].isnull().sum()
            total = len(df)
            cleaned_columns_df = df[col].dropna()

            # 计算统计指标
            stats.append({
                'Column': col,
                'Total Entries': total,
                'Non-Empty Count': total - empty,
                'Empty Count': empty,
                'Non-Empty Ratio (%)': round((total - empty) / total * 100, 2),
                'Avg Length (non-empty)': round(lengths[lengths > 0].mean(), 2),
                'Max Length': lengths.max(),
                'Min Length (non-empty)': cleaned_columns_df.str.len().min()
            })

        # 生成统计DataFrame并保存到实例变量
        self.stats_df = pd.DataFrame(stats)

        # 打印美观的统计结果
        title = " 统计结果汇总 "
        print(f"\n{title:=^50}")
        print(self.stats_df.to_string(index=False))

    def save_result(self) -> None:
        """导出统计结果到Excel"""
        if self.stats_df is not None:
            self.stats_df.to_excel(self.PATH, index=False)
        else:
            print("错误：统计结果未生成，请检查数据或调用 csv_info()")


if __name__ == "__main__":
    information_path = r"column_statistics2.xlsx"
    df_columns = ['Introduction', 'Methodology', 'Conclusion', 'Others']
    df_dataframe = pd.read_csv(r"combined_df2.csv")
    information = CSVInfo(columns=df_columns, dataframe=df_dataframe, path=information_path)
    information.save_result()
