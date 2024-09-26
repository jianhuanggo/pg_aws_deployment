

def chatbot():
    def chatbot_s():
        while True:
            user_input = input("Enter text: ")
            messages.append({"role": "user", "content": f"{user_input}"})
            bot_response = generate_text()
            generate_audio(bot_response)
    return chatbot_s
