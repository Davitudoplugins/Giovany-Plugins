# Userge Plugin for getting list of sites where you can watch a particular Movie or TV-Show
# Author: Sumanjay (https://github.com/cyberboysumanjay) (@cyberboysumanjay)
# All rights reserved.

import os

from justwatch import JustWatch, justwatchapi

from kannax import Message, kannax

# https://github.com/dawoudt/JustWatchAPI/issues/47#issuecomment-691357371
justwatchapi.__dict__["HEADER"] = {
    "User-Agent": "JustWatch client (github.com/dawoudt/JustWatchAPI)"
}

LOGGER = kannax.getLogger(__name__)
WATCH_COUNTRY = os.environ.get("WATCH_COUNTRY", "IN")


def get_stream_data(query):
    stream_data = {}

    # Cooking Data
    just_watch = JustWatch(country=WATCH_COUNTRY)
    results = just_watch.search_for_item(query=query)
    movie = results["items"][0]
    stream_data["title"] = movie["title"]
    stream_data["movie_thumb"] = (
        "https://images.justwatch.com"
        + movie["poster"].replace("{profile}", "")
        + "s592"
    )
    stream_data["release_year"] = movie["original_release_year"]
    try:
        print(movie["cinema_release_date"])
        stream_data["release_date"] = movie["cinema_release_date"]
    except KeyError:
        try:
            stream_data["release_date"] = movie["localized_release_date"]
        except KeyError:
            stream_data["release_date"] = None

    stream_data["type"] = movie["object_type"]

    available_streams = {}
    if movie.get("offers"):
        for provider in movie["offers"]:
            provider_ = get_provider(provider["urls"]["standard_web"])
            available_streams[provider_] = provider["urls"]["standard_web"]

    stream_data["providers"] = available_streams

    scoring = {}
    if movie.get("scoring"):
        for scorer in movie["scoring"]:
            if scorer["provider_type"] == "tmdb:score":
                scoring["tmdb"] = scorer["value"]

            if scorer["provider_type"] == "imdb:score":
                scoring["imdb"] = scorer["value"]
    stream_data["score"] = scoring
    return stream_data


@kannax.on_cmd(
    "ver",
    about={
        "header": "Obtenha os links de onde assistir Séries e Filmes",
        "Como usar": "{tr}ver [query]",
        "Exemplo": "{tr}ver Vingadores Ultimado",
    },
)
async def fetch_watch_sources(message: Message):
    await message.edit("Pesquisando, aguarde ☺️ ...")
    query = message.input_str
    streams = get_stream_data(query)
    title = streams["title"]
    thumb_link = streams["movie_thumb"]
    release_year = streams["release_year"]
    release_date = streams["release_date"]
    scores = streams["score"]
    try:
        imdb_score = scores["imdb"]
    except KeyError:
        imdb_score = None

    try:
        tmdb_score = scores["tmdb"]
    except KeyError:
        tmdb_score = None

    # type = streams['type']
    stream_providers = streams["providers"]
    if release_date is None:
        release_date = release_year

    output_ = f"""
    **TÍTULO ORIGINAL:**\n| 🎬 `{title}`
    \n**Lançamento:** `{release_date}`"""
    if imdb_score:
        output_ = (
            output_
            + f"""
        \n**⭐️ Avaliação no IMDB: **{imdb_score}"""
        )
    if tmdb_score:
        output_ = output_ + f"\n**⭐️ Avaliação no TMDB: **{tmdb_score}"

    output_ = output_ + "\n\n**Disponível em:**\n"
    for provider, link in stream_providers.items():
        if "sonyliv" in link:
            link = link.replace(" ", "%20")
        output_ += f"▫️ [{pretty(provider)}]({link})\n"

    await message.client.send_photo(
        chat_id=message.chat.id,
        photo=thumb_link,
        caption=output_,
        disable_notification=True,
    )
    await message.delete()


# Helper Functions
def pretty(name):
    if name == "play":
        name = "Google Play Movies"
    return name[0].upper() + name[1:]


def get_provider(url):
    url = url.replace("https://www.", "")
    url = url.replace("https://", "")
    url = url.replace("http://www.", "")
    url = url.replace("http://", "")
    url = url.split(".")[0]
    return url
