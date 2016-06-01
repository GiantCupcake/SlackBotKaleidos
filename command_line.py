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
    retire = input("eliminate wrong words by their numbers").split(" ")
    for i in range(len(retire)):
        retire[i] = int(retire[i])
    print(retire)
    eliminated = set()
    for i in range(len(dico)):
        if i in retire:
            eliminated.add(dico[i])
    print(eliminated)
    return eliminated


def clean_words(all_words, eliminated):
    #Clean de chacun des all_words tous les mots contenus dans eliminated
    validated_words = []
    for groups in all_words:
        remaining = []
        for word in groups:
            if word not in eliminated:
                remaining.append(word)
        validated_words.append(remaining)
    return validated_words

#Si on ne voit le mot qu'une fois, on lui assigne la valeur 4,sinon 1
def points_per_words(valid_words):
    valeur = dict()
    for words in valid_words:
        for word in words:
            if word not in valeur:
                valeur[word] = 4
            else:
                valeur[word] = 1
    return valeur

def count_points(group_words,value):
    points = []
    for group in group_words:
        points.append(sum([value[word] for word in group]))
    return points


if __name__ == "__main__":
    #voic choice
    letter = chr(randint(0, 25) + 97)
    #all_words = [[],[],[]]
    all_words = [state_get_words(letter) for _ in range(3)]
    print(all_words)
    #pour le joueur 2
    eliminated = [state_validate_words(all_words[0],all_words[2]) for _ in range(3)]
    validated_words = clean_words(all_words,eliminated)
    word_value = points_per_words(validated_words)
