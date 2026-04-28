import csv

input_file=open('data_delete_attribute.csv','r',encoding='utf-8')
output_file=open('data_switch_into_txt.py','w',encoding='utf-8')
csv_reader = csv.reader(input_file)
processed_cells = []


for row_num, row in enumerate(csv_reader, 1):
        if len(row) >= 3:
            third_column = row[2]  # 提取第三列（索引2）
            original_lines = third_column.split('\n')
            non_empty_indices = [i for i, line in enumerate(original_lines) if line.strip()]
            if len(non_empty_indices) >= 2:
                if non_empty_indices[1] - non_empty_indices[0] == 3:
                    del original_lines[non_empty_indices[0]]
                    non_empty_indices = [i for i, line in enumerate(original_lines) if line.strip()]
                if len(non_empty_indices) >= 2 and non_empty_indices[-1] - non_empty_indices[-2] == 3:
                    del original_lines[non_empty_indices[-1]]
            cell_lines = [line.strip() for line in original_lines if line.strip()]
            cleaned_cell = '\n'.join(cell_lines)
            if cleaned_cell:
                processed_cells.append(cleaned_cell)

final_content = '\n\n'.join(processed_cells)
output_file.write(final_content)


print(f"成功提取第三列！结果已保存到：{output_file}")

input_file.close()
output_file.close()