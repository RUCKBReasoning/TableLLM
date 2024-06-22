import re
import sys
import pandas as pd
from io import StringIO
from docx import Document


def docx2tabular(docxPath):
    doc = Document(docxPath)
    table = doc.tables[0]
    tabular = [[cell.text for cell in row.cells] for row in table.rows]
    return tabular


def save_file(uploadFile):
    base_dir = 'uploaded_files'
    local_path = f'{base_dir}/{uploadFile.file_id}-{uploadFile.name}'
    table_description = ''
    if uploadFile.name.endswith('.csv'):
        # read csv and save to local file
        df = pd.read_csv(uploadFile, encoding="latin-1")
        df.to_csv(local_path, index=False)
        query_tabular = uploadFile.getvalue().decode("utf-8")

    elif uploadFile.name.endswith(('.xlsx', 'xls')):
        # read xlsx and save to local file
        df = pd.ExcelFile(uploadFile).parse()
        if uploadFile.name.endswith('.xlsx'):
            local_path = local_path.replace(".xlsx", ".csv")
            df.to_csv(local_path, index=False)
        else:
            local_path = local_path.replace(".xls", ".csv")
            df.to_csv(local_path, index=False)
        with open(local_path, 'r') as fp:
            query_tabular = fp.read()

    elif uploadFile.name.endswith('.docx'):
        # read docx and save to local file
        with open(local_path, "wb") as fpdf:
            fpdf.write(uploadFile.read())
        tabular_rows = docx2tabular(local_path)
        df = pd.DataFrame(tabular_rows[1:], columns=tabular_rows[0])
        query_tabular = '\n'.join(','.join(row) for row in tabular_rows)

    file_detail = {
        'name': uploadFile.name,
        'local_path': local_path,
        'description': table_description
    }

    return df, query_tabular, file_detail


def preprocess_code(code, local_path, is_merge):
    # code check
    if code.find('plt') != -1:
        savefig = re.findall('plt.savefig\(.*?\)', code)
        for i in savefig:
            code = code.replace(i, '')
        code = code.replace('plt.show()', 'print(plt)')

    content_in_print = re.findall('print\((.*?)\)', code)
    if len(content_in_print) == 0:
        return None
    content_in_print = content_in_print[-1]

    if content_in_print.find('[') != -1:
        variable_in_print = re.findall('[0-9a-zA-Z\_]+\[.*?\]', code)[0]
        code = code.replace(f'print({content_in_print})', '')
        code = code + f'final_result = {variable_in_print}\n\nprint(final_result)'
    else:
        variable_in_print = content_in_print
        while variable_in_print.find(',') != -1:
            variable_in_print = variable_in_print[variable_in_print.find(',') + len(', '):]
        code = code.replace(f'print({content_in_print})', f'print({variable_in_print})')

    # replace file path
    if is_merge:
        code = code.replace('data1.csv', local_path[0])
        code = code.replace('data2.csv', local_path[1]).lstrip('\n').lstrip(' ')
    else:
        code = code.replace('data.csv', local_path).lstrip('\n').lstrip(' ')
    
    return code


def run_code(code, local_path, is_merge=False):
    try:
        # preprocess code
        code = preprocess_code(code, local_path, is_merge)
        if code is None:
            return 'Error occur while running code.'
        
        # run file, get the variables and console output
        sys.stdout = StringIO()
        exec(code)
        variables = locals()
        output_str = sys.stdout.getvalue().rstrip('\n')
        sys.stdout.close()
        sys.stdout = sys.__stdout__  # resume stdout

        # extract variable name from print()
        output_variable_name = re.findall('print\((.*?)\)', code)[0]

        # find the output variable
        output_variable = variables[output_variable_name]
        answer = output_variable

        return answer
    except Exception as e:
        sys.stdout = sys.__stdout__  # resume stdout
        # print(str(e))
        return 'Error occur while running code.'


def check_code(code, local_path, is_merge=False):
    try:
        # replace file path
        code = preprocess_code(code, local_path, is_merge)
        if code is None:
            return False
        
        # run code
        sys.stdout = StringIO()
        exec(code)
        variables = locals()
        sys.stdout.close()
        sys.stdout = sys.__stdout__  # resume stdout

        return True
    except Exception as e:
        sys.stdout = sys.__stdout__  # resume stdout
        # print(str(e))
        return False
