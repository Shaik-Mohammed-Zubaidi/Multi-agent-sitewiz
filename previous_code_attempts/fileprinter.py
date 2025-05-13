# import os

# def print_directory_tree(root_dir, indent=''):
#     for item in os.listdir(root_dir):
#         item_path = os.path.join(root_dir, item)
#         if os.path.isfile(item_path):
#             print(indent + '- ' + item)
#         elif os.path.isdir(item_path):
#             print(indent + '+ ' + item)
#             print_directory_tree(item_path, indent + '  ')

# # Example usage:
# root_directory = './data/databases/debit_card_specializing'  # Current directory
# print_directory_tree(root_directory)

import re
text = "```sql\nSELECT \n    COUNT(CASE WHEN Currency = 'EUR' THEN 1 END) * 1.0 / \n    NULLIF(COUNT(CASE WHEN Currency = 'CZK' THEN 1 END), 0) AS Ratio_EUR_to_CZK\nFROM \n    customers;\n```"
cleaned = re.sub(r"```sql\s*|\s*```", "", text).strip()
print(cleaned)