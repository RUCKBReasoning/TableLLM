QA_PROMPT = """Offer a thorough and accurate solution that directly addresses the Question outlined in the [Question].
### [Table Text]
{table_descriptions}
### [Table]
```
{table_in_csv}
```
### [Question]
{question}
### [Solution]"""

CODE_PROMPT = """Below are the first few lines of a CSV file. You need to write a Python program to solve the provided question.

Header and first few lines of CSV file:
{csv_data}

Question: {question}"""

CODE_MERGE_PROMPT = """Below are the first few lines two CSV file. You need to write a Python program to solve the provided question.

Header and first few lines of CSV file 1:
{csv_data1}

Header and first few lines of CSV file 2:
{csv_data2}

Question: {question}"""

LLAMA2_PROMPT = "[INST]{prompt}[/INST]"
