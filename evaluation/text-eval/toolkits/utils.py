import re

def normalize_answer(s):
    s = s.lower()
    s = s.strip()
    s = s.replace(',','')
    s = s.replace('and','')
    s = s.replace('  ',' ')
    s = s.replace("'", "")
    s = s.replace("\"", "")

    number_words = {
        r'\bone\b': '1',
        r'\btwo\b': '2',
        r'\bthree\b': '3',
        r'\bfour\b': '4',
        r'\bfive\b': '5',
        r'\bsix\b': '6',
        r'\bseven\b': '7',
        r'\beight\b': '8',
        r'\bnine\b': '9',
        r'\bten\b': '10'
    }
    for word, number in number_words.items():
        s = re.sub(word, number, s)
    # s = s.replace(' ','')
    #s = s.replace('.','')
    s = s.replace('–','-')
    s = s.replace('-','-')
    s = s.replace('*','')
    return s

def can_convert_to_number(s):
    # check if a string can be converted to a number
    try:
        int(s)
        return True
    except ValueError:
        pass  

    try:

        float(s)
        return True
    except ValueError:
        
        return False
    

def extract_keywords_and_numbers(reference):
    keywords = []
    numbers = []

    if bool(re.search(r'\d', reference[0])):
        #numbers = [re.sub(r'[^0-9.+-]', '', num) for num in reference]
        numbers = []
        for num in reference:
            # Use regular expressions to match all possible numbers (including those with decimal points and plus or minus signs)
            possible_numbers = re.findall(r'[-+]?[0-9]*\.?[0-9]+', num)
            cleaned_numbers = []
            for possible_num in possible_numbers:
                # Remove non-numeric characters from the numbers (except for the decimal point and the plus or minus sign)
                cleaned_num = re.sub(r'[^0-9.+-]', '', possible_num)
                
                cleaned_numbers.append(cleaned_num)
        
            numbers += cleaned_numbers
    else:
        keywords = reference


    return keywords, numbers

def calculate_relative_error(reference_value, assistant_value):
    # A function for calculating the relative error
    if reference_value == 0:
        return float('inf')  
    return abs((reference_value - assistant_value) / reference_value)


def exact_match(reference_answer, assistant_answer):
    # Extract key words and numerical values
    keywords, numbers = extract_keywords_and_numbers(reference_answer)

    is_match = False
    if keywords != []:
        # Check if all the keywords are in assistant_In the answer
        is_match = all(keyword in assistant_answer for keyword in keywords)
    elif numbers != []:
        assistant_numbers = [float(num) for num in re.findall(r'[-+]?[0-9]*\.?[0-9]+', assistant_answer)]
        reference_numbers = [float(num) for num in numbers]
        # Check if all the values are in assistant_In the answer    
        is_match = all(any(calculate_relative_error(ref_num, assistant_num) <= 0.01 or round(abs(assistant_num)) == abs(ref_num) or (ref_num*1000 == assistant_num) or (assistant_num*1000 == ref_num) for assistant_num in assistant_numbers) for ref_num in reference_numbers)

    return is_match
