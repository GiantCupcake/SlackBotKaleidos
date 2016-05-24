from random import randint
import time

def state_get_words(letter):
    words = []
    while True:
        word = input("give me a word starting with : " + letter + " ").lower()
        if not word.strip():
            break
        if word in words or not word.startswith(letter):
            continue
        words.append(word)
    print("Tes mots sont : {}".format(", ".join(words)))
    return words


def state_validate_words(*words):
    #On veut éliminer les doublons
    dico = []
    for attr in words:
        for word in attr:
            if word not in dico:
                dico.append(word)
    print(dico)
    return dico

def state_count_points():
    pass


if __name__ == "__main__":
    #voic choice
    letter = chr(randint(0, 25) + 97)
    words = [state_get_words(letter) for _ in range(3)]
    print(words)
    #pour le joueur 2
    stateValidateWords[words[0],words[2]]
    #for _ in range(3)
    #        stateValidateWords(words)
    #stateCountPoints()
