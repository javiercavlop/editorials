from collections import Counter
import shelve, os
from django.db.models import Count, OuterRef, Subquery
from app.models import UserCategory, Book, Category, Rating
from .utils.Timer import Timer
from math import sqrt
from django.conf import settings

RATINGS_RS = "data/rs/ratings/dataRS.dat"
CATEGORIES_RS = "data/rs/categories/dataRS.dat"

def load_categories_rs():
    timer = Timer()
    timer.start()
    print("----------------------LOADING CATEGORIES RS-----------------------")
    if not os.path.exists(settings.CATEGORIES_DIR):
        os.makedirs(settings.CATEGORIES_DIR, exist_ok=True)
    shelf = shelve.open(CATEGORIES_RS)
    book_categories = get_book_categories()
    shelf['similarities'] =  book_categories
    shelf.close()
    timer.stop()
    print("El tiempo de ejecución ha sido de %f milisegundos" % (timer.get_time()))

def get_categories_recommendations(user_categories):
    shelf = shelve.open(CATEGORIES_RS)
    book_categories = shelf['similarities']
    shelf.close()
    return compute_categories_similarities(book_categories, user_categories)

def compute_categories_similarities(book_categories, user_categories):
    result = {}
    for b in book_categories:
        result[b] = dice_coefficient(user_categories, book_categories[b])
    return sorted(result, key=lambda x: result[x], reverse=True)

def get_book_categories():
    return {book.id: set(book.categories.all()) for book in Book.objects.all() if book.categories.all().exists()}

def dice_coefficient(set1, set2):
    return 2 * len(set1.intersection(set2)) / (len(set1) + len(set2))

def load_ratings_rs():
    timer = Timer()
    timer.start()
    print("----------------------LOADING RATINGS RS-----------------------")
    Prefs={}
    if not os.path.exists(settings.RATINGS_DIR):
        os.makedirs(settings.RATINGS_DIR, exist_ok=True)
    shelf = shelve.open(RATINGS_RS)
    ratings = Rating.objects.all()
    for rating in ratings:
        user_id = rating.user.id
        book_id = rating.book.id
        rating = rating.rating
        Prefs.setdefault(user_id, {})
        Prefs[user_id][book_id] = rating
    shelf['Prefs']=Prefs
    shelf['ItemsPrefs']=transform_prefs(Prefs)
    shelf.close()
    timer.stop()
    print("El tiempo de ejecución ha sido de %f milisegundos" % (timer.get_time()))

def sim_distance(prefs, person1, person2):
    si = {}
    for item in prefs[person1]: 
        if item in prefs[person2]: si[item] = 1

        if len(si) == 0: return 0

        sum_of_squares = sum([pow(prefs[person1][item] - prefs[person2][item], 2) 
                    for item in prefs[person1] if item in prefs[person2]])
        
        return 1 / (1 + sum_of_squares)

def sim_pearson(prefs, p1, p2):
    si = {}
    for item in prefs[p1]:
        if item in prefs[p2]:
            si[item] = 1

    if len(si) == 0: return 0

    n = len(si)

    sum1 = sum([prefs[p1][it] for it in si])
    sum2 = sum([prefs[p2][it] for it in si])

    sum1Sq = sum([pow(prefs[p1][it], 2) for it in si])
    sum2Sq = sum([pow(prefs[p2][it], 2) for it in si])	

    pSum = sum([prefs[p1][it] * prefs[p2][it] for it in si])

    num = pSum - (sum1 * sum2 / n)
    den = sqrt((sum1Sq - pow(sum1, 2) / n) * (sum2Sq - pow(sum2, 2) / n))
    if den == 0: return 0

    r = num / den

    return r

def get_top_matches(prefs, person, n=10, similarity=sim_pearson):
    scores = [(similarity(prefs, person, other), other) 
                for other in prefs if other != person]
    scores.sort()
    scores.reverse()
    return scores[0:n]

def get_ratings_recommendations(user):
    shelf = shelve.open(RATINGS_RS)
    Prefs = shelf['Prefs']
    shelf.close()
    if int(user.id) not in Prefs:
        return None
    rankings = get_recommendations(Prefs, int(user.id))
    if not rankings:
        return None
    return sorted(rankings, key=lambda x: x[0], reverse=True)

def get_recommendations(prefs, person, similarity=sim_pearson):
    totals = {}
    simSums = {}
    for other in prefs:
        if other == person: continue
        sim = similarity(prefs, person, other)
        if sim <= 0: continue
        for item in prefs[other]:
            if item not in prefs[person] or prefs[person][item] == 0:
                totals.setdefault(item, 0)
                totals[item] += prefs[other][item] * sim
                simSums.setdefault(item, 0)
                simSums[item] += sim

    rankings = [(total / simSums[item], item) for item, total in totals.items()]
    rankings.sort()
    rankings.reverse()
    return rankings

def transform_prefs(prefs):
    result = {}
    for person in prefs:
        for item in prefs[person]:
            result.setdefault(item, {})
    
            result[item][person] = prefs[person][item]
    return result

def calculate_similar_items(prefs, n=10):
    result = {}
    itemPrefs = transform_prefs(prefs)
    c = 0
    for item in itemPrefs:
        c += 1
        if c % 100 == 0: print ("%d / %d" % (c, len(itemPrefs)))
        scores = get_top_matches(itemPrefs, item, n=n, similarity=sim_distance)
        result[item] = scores
    return result

def get_books_recommendations(book):
    shelf = shelve.open(RATINGS_RS)
    ItemsPrefs = shelf['ItemsPrefs']
    shelf.close()
    rankings = get_top_matches(ItemsPrefs, int(book.id),n=10,similarity=sim_distance)
    if not rankings:
        return None
    
    return sorted(rankings, key=lambda x:x[1], reverse=True)

def get_recommended_items(prefs, itemMatch, user):
    userRatings = prefs[user]
    scores = {}
    totalSim = {}
    for (item, rating) in userRatings.items():
        for (similarity, item2) in itemMatch[item]:
            if item2 in userRatings: continue
            scores.setdefault(item2, 0)
            scores[item2] += similarity * rating
            totalSim.setdefault(item2, 0)
            totalSim[item2] += similarity

    try:
        rankings = [(score / totalSim[item], item) for item, score in scores.items()]
    except ZeroDivisionError:
        rankings = []

    rankings.sort()
    rankings.reverse()
    return rankings
