import tweepy

# Configura le chiavi API
API_KEY = "lZ3La0Z1WHnD6xBLpFsnFiMBg"
API_SECRET = "KcUMLXESqLJEfjCG2bxruXfHBwHuRsQPg56cihWmdj2QsHGgSj"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAORlyQEAAAAAm71HoGDgJDGfOQVUkZK1raCNpYw%3DrJpZov8et1HnNdI2x8oBW2rTrrJJ3TceZRNqcodS9FwrYiwqK1"

# Autenticazione tramite Bearer Token (solo lettura)
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Parola target
query = "Culo -is:retweet lang:it"  # Cerca "Culo" nei tweet in italiano, escludendo i retweet


# Recupera i tweet
def fetch_tweets(query, max_results=100):
    try:
        # Esegui la ricerca
        response = client.search_recent_tweets(query=query, max_results=max_results, tweet_fields=["text", "author_id"])
        tweets = response.data

        if not tweets:
            print("Nessun tweet trovato.")
            return []

        # Estrai le frasi dai tweet
        phrases = [{"number": i + 1, "text": tweet.text} for i, tweet in enumerate(tweets)]

        # Mostra i risultati
        print(f"Raccolti {len(phrases)} tweet:")
        for phrase in phrases:
            print(f"{phrase['number']}. {phrase['text']}")

        return phrases
    except Exception as e:
        print("Errore durante il recupero dei tweet:", e)
        return []


# Recupera i tweet
tweets = fetch_tweets(query)


# Salva i risultati in un file TSV
def save_to_tsv_with_numbers(tweets, file_name):
    try:
        df = pd.DataFrame(tweets)
        df.to_csv(file_name, sep="\t", index=False, encoding="utf-8", header=False)
        print(f"Tweet salvati in {file_name}")
    except Exception as e:
        print(f"Errore durante il salvataggio del file: {e}")


# Salva in un file TSV con numerazione
if tweets:
    save_to_tsv_with_numbers(tweets, "tweets_collected.tsv")