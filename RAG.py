from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

import base64
import numpy as np
import pandas as pd
import faiss
import pickle

from cassandra.cluster import Cluster

# Cassandra config
cluster = Cluster(['localhost'], port=9042)
session = cluster.connect()
session.set_keyspace('chatbot')
cassandra_tablename = "documents"
print("[RAG] Connect cassandra")

# Models config
retriever_model="all-MiniLM-L6-v2"
retriever = SentenceTransformer(retriever_model)
dummy = retriever.encode(["dummy input"])
dimension = dummy[0].shape[0]
index = faiss.IndexFlatL2(dimension)

client = OpenAI(
    api_key= "<INSERT OPENAI API HERE>"
)

def base64toNumpy(base64_str):
    r = base64.b64decode(base64_str)
    q = pickle.loads(r)
    return np.array(q)

def faiss_dense_retrieval(prompt):
    r = session.execute("SELECT * FROM documents")
    df = pd.DataFrame(r)

    # Prepare FAISS index
    chunks = df["chunk"]
    urls = df["url"]
    embeddings = np.array([base64toNumpy(x) for x in df["embed"]])
   
    index.add(embeddings)

    # Query FAISS
    query_embedding = retriever.encode([prompt])
    distances, indices = index.search(query_embedding, 3)
    return [chunks[i] for i in indices[0]], [urls[i] for i in indices[0]]

def generate_answer_with_chatgpt(retrieved_chunks, prompt, history):
    combined_prompt = """
    Task:
    I want you to answer these question base on the contexts and History Chat. 
    If the information in the context and history partially relates to the questions. I want you to think more and extract relevance part and answer as best as the context imply. 
    If only the information is totally unrelated to the question, answer i dont have any information.
    
    History Chat:
    {}
    
    Context:
    {}

    Question:
    {}

    Answer:
    """.format("\n\n".join(retrieved_chunks), "\n\n".join(history), prompt)
    
    response = client.chat.completions.create(
        messages= [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": combined_prompt},
        ],
        model="gpt-4o",
    )
    # print(response)
    return response.choices[0].message.content.strip()
    

def rag_retrieval_qa(prompt, history):
    """
    Perform Retrieval-Augmented Generation (RAG) with hybrid and hierarchical retrieval using ChatGPT API.

    Args:
        content_dict (dict): A dictionary where keys are IDs and values are content strings.
        prompt (str): The prompt/question to answer.

    Returns:
        str: The answer generated by ChatGPT based on the most relevant content.
    """

    retrieved_chunks, retrieved_url = faiss_dense_retrieval(prompt)
    answer = generate_answer_with_chatgpt(retrieved_chunks, prompt, history)

    return answer, retrieved_chunks, retrieved_url

# Example usage
if __name__ == "__main__":
    content = {
        "1": "Python is a programming language that lets you work quickly and integrate systems more effectively.",
        "2": "Machine learning is a method of data analysis that automates analytical model building.",
        "3": "Transformers are deep learning models that adopt the mechanism of self-attention.",
        "4": '''
        Here are detailed descriptions of three famous cities in the world: New York City, Paris, and Tokyo.

---

### **New York City, USA**
New York City, often referred to as "The Big Apple," is one of the most iconic cities in the world, renowned for its cultural diversity, towering skyscrapers, and vibrant atmosphere. Located in the state of New York, it is the most populous city in the United States, home to over 8 million residents. The city comprises five boroughs: Manhattan, Brooklyn, Queens, The Bronx, and Staten Island. Manhattan is the heart of NYC, where landmarks such as the Empire State Building, Central Park, and Times Square draw millions of visitors annually. The city's skyline is a symbol of architectural achievement, with structures like the One World Trade Center standing as testaments to resilience and progress.

New York City is a global hub for finance, with Wall Street and the New York Stock Exchange located in the Financial District. It is also a cultural epicenter, housing world-class institutions such as the Metropolitan Museum of Art, the American Museum of Natural History, and Broadway theaters. The diversity of its residents makes NYC a melting pot of cuisines, traditions, and languages, with vibrant neighborhoods like Chinatown, Little Italy, and Harlem offering unique experiences. The city never sleeps, offering entertainment, shopping, and dining options 24/7. The annual New Year's Eve celebration at Times Square, complete with the iconic ball drop, is a globally televised event that attracts millions in person and online.

---

### **Paris, France**
Paris, often called "The City of Light," is synonymous with romance, art, and history. Located along the Seine River in northern France, Paris is the nation's capital and a global beacon of culture, fashion, and gastronomy. The city's historical and architectural landmarks, including the Eiffel Tower, Notre-Dame Cathedral, and the Louvre Museum, attract millions of visitors from around the world each year. The Louvre, the world’s largest art museum, is home to masterpieces like the Mona Lisa and the Venus de Milo, showcasing Paris's deep connection to artistic heritage.

Paris is also famous for its charming streets, lined with Haussmannian buildings, cafes, and boutiques. The Champs-Élysées, often referred to as "the most beautiful avenue in the world," leads to the iconic Arc de Triomphe, which stands as a tribute to French military victories. Montmartre, a historic district perched on a hill, is known for its bohemian spirit and the Basilica of the Sacré-Cœur. The Seine River, which runs through the city, is adorned with picturesque bridges and is best explored by boat. Paris is also a global center for haute couture, with fashion houses like Chanel, Dior, and Louis Vuitton setting global trends.

French cuisine is a cornerstone of Parisian culture, with Michelin-starred restaurants and quaint bistros serving classic dishes like coq au vin, escargot, and crème brûlée. The city is also known for its wine and patisseries, offering delights like croissants and macarons. Paris’s influence extends to literature, cinema, and philosophy, having been home to figures like Victor Hugo, Simone de Beauvoir, and Ernest Hemingway. Its timeless charm continues to captivate travelers and residents alike.

---

### **Tokyo, Japan**
Tokyo, the capital of Japan, is a dynamic metropolis that seamlessly blends ultramodern innovation with deep-rooted tradition. As one of the largest cities in the world by population, Tokyo is a bustling hub of technology, culture, and commerce. The city is known for its towering skyscrapers, neon-lit streets, and efficient public transportation system, including the world-famous Shinkansen bullet trains. At the same time, Tokyo preserves its historical heritage, with ancient temples, shrines, and traditional neighborhoods offering a glimpse into Japan's past.

Landmarks such as the Tokyo Skytree and Tokyo Tower provide stunning views of the sprawling cityscape, while historic sites like the Meiji Shrine and Senso-ji Temple offer moments of tranquility amid the urban energy. The Imperial Palace, surrounded by beautiful gardens, stands as a symbol of Japan's monarchy. Tokyo is also a global trendsetter in fashion and technology, with districts like Harajuku and Akihabara drawing enthusiasts from around the world. Harajuku is synonymous with youth culture and avant-garde fashion, while Akihabara is a haven for tech gadgets and anime culture.

Culinary experiences in Tokyo are unparalleled, with everything from Michelin-starred sushi restaurants to casual ramen shops. The Tsukiji Fish Market, known for its fresh seafood, is a must-visit for food enthusiasts. Tokyo also boasts an active nightlife scene, with karaoke bars, izakayas, and live music venues catering to all tastes. Despite its modernity, the city values nature, with cherry blossoms in Ueno Park and the Meiji Jingu Gaien offering seasonal beauty. Tokyo’s ability to honor its past while embracing the future makes it a truly unique destination.

---

These cities represent the pinnacle of cultural richness, global influence, and unique experiences, each offering something extraordinary to visitors and residents alike.
        ''',
        "5": '''
        African Elephant
The African elephant (Loxodonta africana) is the largest land animal on Earth, known for its massive size, intelligence, and social structure. Males can reach up to 4 meters in height and weigh over 6,000 kilograms, while females are slightly smaller. Their most iconic feature is their long, dexterous trunk, which has over 40,000 muscles and serves as a versatile tool for grabbing food, drinking water, and communicating with other elephants. African elephants are herbivores, consuming up to 150 kilograms of vegetation daily, including leaves, bark, and fruit. They play a vital role in their ecosystem by dispersing seeds and creating pathways through dense vegetation, benefiting other species.

Fun Fact: Elephants have incredible memories. Matriarchs, the leaders of their herds, can recall locations of water sources and safe routes, even after decades. Additionally, their ears act as cooling systems, helping regulate body temperature in the scorching African heat. Did you know an elephant’s trunk can hold up to 8 liters of water? This makes them highly adept at staying hydrated in arid environments.

Peregrine Falcon
The peregrine falcon (Falco peregrinus) holds the title of the fastest bird in the world, capable of reaching speeds over 240 mph (386 km/h) during its characteristic hunting dive, called a stoop. Found on every continent except Antarctica, peregrine falcons thrive in diverse habitats ranging from urban skyscrapers to remote cliffs. They are medium-sized raptors with blue-gray backs, barred white undersides, and a distinctive black "moustache" marking on their face. These falcons primarily feed on other birds, such as pigeons and ducks, which they catch mid-air with unmatched precision.

Fun Fact: Peregrine falcons were once endangered due to the widespread use of DDT pesticides, but conservation efforts have helped their populations recover dramatically. Today, they are a symbol of resilience and adaptability, even nesting in urban areas where tall buildings mimic their natural cliffside habitats. Amazingly, their eyesight is so sharp they can spot prey from over 3 kilometers away!

Giant Panda
The giant panda (Ailuropoda melanoleuca), native to the mountainous forests of central China, is a global symbol of wildlife conservation. Despite being a member of the carnivore family, pandas primarily consume bamboo, with their diet consisting of about 99% of this tough, fibrous plant. An adult panda spends 10–16 hours daily eating to meet its nutritional needs, consuming up to 40 kilograms of bamboo shoots, stems, and leaves. They are solitary animals, using their keen sense of smell to avoid or locate other pandas.

Fun Fact: The giant panda’s black-and-white fur is not just for show—it helps them camouflage in their snowy and shadowy forest habitats. Pandas have an extra "thumb," an extended wrist bone, which aids in gripping bamboo stalks. Did you know that panda cubs are born pink, blind, and only weigh about 100 grams? They grow rapidly, reaching up to 100 kilograms as adults.
            ''',
        "6": '''
        Baobab Tree
The baobab tree (Adansonia), often called the "Tree of Life," is one of the most iconic trees in Africa, with some species also found in Madagascar and Australia. Known for its unique, swollen trunk that can store thousands of liters of water, the baobab thrives in arid and semi-arid climates where water is scarce. These majestic trees can live for over 1,000 years, with some specimens believed to be as old as 2,500 years. The baobab's bark is smooth and grayish, while its sparse branches resemble roots, giving it the nickname "upside-down tree." Its fruit, commonly called monkey bread, is highly nutritious, packed with vitamin C, antioxidants, and fiber.

Fun Fact: Baobabs are ecological powerhouses, supporting a wide range of wildlife. Birds often nest in their hollow trunks, bats and bees feed on their flowers, and animals like elephants and baboons consume their fruit. Baobabs also play a central role in local folklore and culture, often seen as sacred symbols of wisdom and resilience. Did you know the baobab flowers open only at night and are pollinated by bats? This nocturnal pollination is a fascinating adaptation to their environment.

Redwood Tree
The redwood tree (Sequoia sempervirens) is a living testament to nature’s grandeur, dominating the coastal forests of California and Oregon. These towering giants can grow over 100 meters tall, making them the tallest trees on Earth. Redwoods are incredibly resilient, with bark up to 30 centimeters thick that protects them from fire, insects, and disease. They thrive in foggy environments, absorbing moisture directly from the air through their leaves and bark. These ancient trees are a key component of their ecosystem, supporting diverse species of plants, birds, and mammals.

Fun Fact: Some redwoods are over 2,000 years old, meaning they were already standing when Julius Caesar was alive! Their root systems are surprisingly shallow, but they intertwine with those of neighboring redwoods, creating a stable network that helps them withstand strong winds and floods. Did you know that if a redwood tree falls, it can sprout new trees from its base, allowing the same genetic line to thrive for millennia?

Banyan Tree
The banyan tree (Ficus benghalensis) is a marvel of nature, famous for its sprawling canopy and aerial roots that grow into the ground to form new trunks. Native to India and Southeast Asia, this tree can cover an area of several acres, creating a natural cathedral of shade. Its branches are lined with glossy green leaves, and its figs provide food for a variety of animals, including birds, monkeys, and bats. The banyan tree holds a special place in many cultures and religions, often symbolizing eternal life and spiritual enlightenment.

Fun Fact: The Great Banyan Tree in Kolkata, India, is one of the largest trees in the world by area, spreading over 3.5 acres! Banyans are also known for their medicinal properties; their leaves, bark, and roots are used in traditional remedies for various ailments. Did you know banyan trees can live for centuries, with some living examples estimated to be over 500 years old? Their ability to create vast, self-sustaining groves makes them an incredible force of nature.
            '''
    }
    question = "Give me some good comment on docln.net"

    response = rag_retrieval_qa(question, [])
    print(response)
