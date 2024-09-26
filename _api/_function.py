import requests


# def get_order_details(order_id):
#     # https://www.youtube.com/watch?v=pI1yUiNKyDA&t=1138s
#     url = "http://your_api_endpoint/order_info"  # Replace with your actual endpoint
#     params = {'order_id': order_id}
#     headers = {"accept": "application/json", "Content-Type": "application/json"}
#     response = requests.post(url, headers=headers, params=params)
#
#     if response.status_code == 200:
#         return response.json()['Result'][0]
#     else:
#         return f"Error: Unable to fetch order details. Status code: {response.status_code}"

def get_order_details(order_id):
    # https://www.youtube.com/watch?v=pI1yUiNKyDA&t=1138s

    return {"order_id": 14, "status": "completed", "shipping": "USPS", "tracking_number": "9400110898825021456930"}

