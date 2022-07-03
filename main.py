import multiprocessing
import random
import time
import numpy as np
import praw
import openai
import pickle

"""A class that represents a Reddit comment.

.. include:: ../../typical_attributes.rst

================= =================================================================
Attribute         Description
================= =================================================================
``author``        Provides an instance of :class:`.Redditor`.
``body``          The body of the comment, as Markdown.
``body_html``     The body of the comment, as HTML.
``created_utc``   Time the comment was created, represented in `Unix Time`_.
``distinguished`` Whether or not the comment is distinguished.
``edited``        Whether or not the comment has been edited.
``id``            The ID of the comment.
``is_submitter``  Whether or not the comment author is also the author of the
                  submission.
``link_id``       The submission ID that the comment belongs to.
``parent_id``     The ID of the parent comment (prefixed with ``t1_``). If it is a
                  top-level comment, this returns the submission ID instead
                  (prefixed with ``t3_``).
``permalink``     A permalink for the comment. :class:`.Comment` objects from the
                  inbox have a ``context`` attribute instead.
``replies``       Provides an instance of :class:`.CommentForest`.
``saved``         Whether or not the comment is saved.
``score``         The number of upvotes for the comment.
``stickied``      Whether or not the comment is stickied.
``submission``    Provides an instance of :class:`.Submission`. The submission that
                  the comment belongs to.
``subreddit``     Provides an instance of :class:`.Subreddit`. The subreddit that
                  the comment belongs to.
``subreddit_id``  The subreddit ID that the comment belongs to.
================= =================================================================

.. _unix time: https://en.wikipedia.org/wiki/Unix_time


"""


def reply(comment_, output_, debug=False):  # change here for bot to actually reply
    if random.random() < 0.25:
        output_ += " *asthmatic cough*"  # to add some variety to grievous
    if not debug and len(comment_.body) < 200:
        try:
            comment_.reply(body=output_)
        except:
            pass


def depth_distance(comm):
    depth = 1
    while comm.parent_id[1] != "3":
        depth += 1
        comm = comm.parent()
    parent_comm = comm
    parent_post = comm.parent()
    distance = 1
    for _comm in parent_post.comments:
        distance += 1
        if _comm == parent_comm:
            break
        for repl in _comm.replies:
            distance += 1
            for _repl in repl.replies:
                distance += 1
    return depth, distance


def get_chance_to_reply(comm):
    try:
        depth, distance = depth_distance(comm)
        dist = 0.5 * ((1 - (1 / (1 + 1.1 / np.exp(0.1 * depth)))) - distance / 50)
        if dist < 0:
            dist = 0.01
    except:
        dist = 0.01
    return dist


class Lars:
    def __init__(self):
        self.reddit = praw.Reddit('botsbot')

        self.subreddit = self.reddit.subreddit("prequelmemes")
        self.triggers = ["tatooine", "lars", "luke", "train", "father", "trained", "ben kenobi"]
        self.blacklist = []
        print("Lars started..")

    def flat_sentence(self, x_):
        t = [x for x in x_]
        # print(x_)
        newt = []
        for x in t:
            if type(x) == str:
                newt.append([(_x, x_.label()) for _x in x_])
            else:
                newt.append(self.flat_sentence(x))
        return newt

    def flat(self, x):
        match x:
            case []:
                return []
            case [[*sublist], *r]:
                return [*self.flat(sublist), *self.flat(r)]
            case [h, *r]:
                return [h, *self.flat(r)]

    def extract_subject(self, tree):
        ret_list = []
        flat_tree = self.flat(self.flat_sentence(tree))
        for i, verb in enumerate(flat_tree[::2]):
            if flat_tree[i * 2 + 1] in ["NN", "NNP"] and "'" not in verb and "’" not in verb:  # "VBP"]
                ret_list.append("".join([x if x in "abcdefghijklmnopqrstuvwxyz" else "" for x in verb.lower()]))

        return ret_list

    openai.api_key = open("apikey.txt").read()

    def get_answer(self, sentence, author):
        try:
            # subject = random.choice(self.extract_subject(self.parser.parse(sentence)))
            if sentence[-1] != ".":
                sentence = sentence + "."
            you = " you" if random.random() < 0.45 else ""
            response = openai.Completion.create(
                model="text-davinci-002",
                prompt=f"Ask a sarcastic question to the statement, made by person by the name of {author}, so it looks"
                       f"like a dialogue. The question must end with a question mark.\n\n{sentence}\nLike{you}",
                temperature=0.3,
                max_tokens=1000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            if len(response.split(" ")) <= 2:
                return None
            response = f"Like{you}" + response["choices"][0]["text"]
            response += "\n\n^(If you dont like my response [have a kitten](" \
                        "https://www.vets4pets.com/siteassets/species/cat/kitten/tiny-kitten-in-sunlight.jpg)) "
            return response

        except:
            # print("No verbs..")
            return None

    def get_bot_output_advanced(self, comment_text_, author):
        return self.get_answer(comment_text_, author)

    def loop(self):
        for comment in self.subreddit.stream.comments(skip_existing=True):
            time.sleep(3)
            author = comment.author
            comment_text = comment.body.split(".")
            comment_text = comment_text[comment_text.index(max(comment_text))]  # we pick the longest
            if "!ignoreall" in comment_text:
                self.blacklist.append(author)
                continue
            if random.random() < get_chance_to_reply(comment) and 150 > len(
                    comment.body) > 8 and "https" not in comment.body:
                # print("1: ", comment_text)
                found = False
                for x in self.triggers:
                    if x.lower() in comment_text.lower():
                        found = True
                        break
                if found and author not in self.blacklist and "bot" not in str(author).lower():
                    _output = self.get_bot_output_advanced(comment_text, author.name)
                    if _output is not None:
                        _output = _output.replace("  ", " ")
                        try:
                            comment.reply(body=_output)
                        except Exception as e:
                            print(f"caught exception {e} on reply ", _output)
                else:
                    pass

    def __call__(self, *args, **kwargs):
        while True:
            try:
                self.loop()
            except Exception as e:
                print(f"caught {e}, sleeping")
                time.sleep(60 * 60)  # 1 hour


class Grievous:
    def __init__(self):
        self.replies = \
            {
                "I don't like sand": ["You fool! I really like taking a bath on tatooine"],
                "bad bot": ["*asthmatic cough*", "You think you can defeat me? You’re nothing."],
                "good bot": ["I thought I couldn't love anyone, but you.."],
                "war crimes": ["Army or not, you must realize, you are doomed!",
                               "Time to abandon ship *abandons ship*"],
                "get offended": ["Time to abandon ship *abandons ship*"],
                "hello there": ["General username!"],
                "general kenobi": ["Hey that's my phrase"],
                "drip": ["Your training has served me well. It has awarded me many nice hats.",
                         "Your outfit will make a fine addition to my collection!",
                         "Be thankful, username, that you have not found yourself in my wardrobe. Your ship is waiting.",
                         "You Fool. I have been decked out in the finest attire... by Count Dooku.",
                         "Respect the drip, Jedi. You have no idea of the power that is in my grasp.",
                         "Your drip is weak. You need only gaze on me to see that."],
                "roger roger": ["*sighs* fools!"],
                "russia": ["Ах, родина", "кто-то сказал *россия*?"],
                "your move": ["You Fool. I have been trained in your Jedi Arts.. by Count Dooku."],
                "viceroy": ["Be thankful, Viceroy, that you have not found yourself in my grip."],
                "kill him": ["I’m no errand boy."],
                "weebs": ["Crush them! Make them suffer!"],
                "grievous": ["yeah thats me",
                             "How does it feel to die?",
                             "Hello there!",
                             ],
                "youngling": ["ah yes, the young jedi scum"]
            }
        self.blacklist = [
            "The-Guild",
            "ltuugze3",
            "Droid-Control",
            "g8nv2glf",
            "SirLexmarkThePrinted",
            "t2wmf",
            "lod_ne",
            "lh1o5",
            "DarthJaderYT",
            "5tobtu00",
            "Octo_05",
            "5ehacawo",
            "doog_tfarceniM",
            "7k09xk86",
            "OazMobile",
            "8lzgu1vf",
            "zpazzy",
            "3d32gjjl",
            "sabmastema",
            "6b06p1j5",
            "KyleTheCookie",
            "10aafo",
            "NJ_Legion_Iced_Tea",
            "7saoya6",
            "hypeforhalo6",
            "bxkoqv7t",
            "Tilretas",
            "fu2vxbn",
            "Kadus500",
            "3zqfymoo",
            "shitdobehappeningtho",
            "az7b12kj",
            "Anakin_Groypwalker",
            "118tkpv4",
            "annomynous23",
            "8oq09lpo",
            "C-TAY116",
            "7i14kydi",
            "kersegum",
            "8r593ptx",
            "Fishwithbrushes",
            "63p7uboo",
            "Galihan",
            "7gf6p",
            "QualifiedApathetic",
            "21iadwei",
            "Dontinsultautomod",
            "c4gaamzy",
            "therealhardscoper",
            "kdx0g",
            "motorblonkwakawaka",
            "2k80x8hp",
            "CryOpposite1666",
            "94qkf12r",
            "hayesboys3",
            "7ctqx",
            "Gabe_Newells_Penis",
            "acs34",
            "Darth_Alpha",
            "mz2f8",
            "alkmaar91",
            "1708vc",
            "GenericUsername935",
            "2me1cihr",
            "Jason1143",
            "242gplak",
            "CoruscantGuardFox",
            "1aclt5qz",
            "RavioliGale",
            "3bx5zw9p",
            "XZEKKX",
            "bcdmj",
            "WhoRoger",
            "1364kh",
            "doomdino65",
            "3mug6yvn",
            "Vanskid5",
            "h3uml",
            "ShoeEntire6638",
            "85bmw3bp",
            "PL4NE_22",
            "5a3wl9kl",
            "LollymitBart",
            "3tuq08iu",
            "Patrickrk",
            "yolme",
            "NewDV",
            "h4565ev5",
            "Harukakonishi",
            "5g6otony",
            "Silvaranth",
            "d04h6493",
            "Mrfoxsin",
            "10k1zc4q",
            "bell37",
            "bim4f",
            "FreddyPlayz",
            "3h5vcb5g",
            "FineGrainsOfSand",
            "4yhdhr4",
            "ElyFlyGuy",
            "176oig",
            "TsunGeneralGrievous",
            "3ksyeolc",
            "CautiousTeam3220",
            "916tetur",
            "unovayellow",
            "4vcydu3r",
            "waitingtodiesoon",
            "kna8y"
        ]

        self.reddit = praw.Reddit('grievousbot')

        self.subreddit = self.reddit.subreddit("prequelmemes")
        print("Grievous started..")
        try:
            with open('stored_comments.pkl', 'rb') as f:
                self.stored_comments = pickle.load(f)
                print("stored comments of len: ", len(self.stored_comments))
        except EOFError:
            self.stored_comments = []

    def __call__(self, *args, **kwargs):
        while True:
            try:
                for comment in self.subreddit.stream.comments(skip_existing=True):
                    author = comment.author
                    comment_text = comment.body
                    if "!ignoreall" in comment_text:
                        self.blacklist.append(author)
                        continue
                    if "grievous" not in str(author).lower() and str(
                            author) not in self.blacklist and random.random() < 0.2 and "bot" \
                            not in str(author).lower():
                        if "lightsabre" in comment_text or "lightsaber" in comment_text:
                            self.stored_comments.append(
                                {
                                    "author": author.name,
                                    "comment": comment_text
                                }
                            )
                            with open('stored_comments.pkl', 'wb') as f:
                                pickle.dump(self.stored_comments, f, pickle.HIGHEST_PROTOCOL)
                            output = f"Ah, a lightsaber comment! \n" \
                                     f"Your comment will make a fine addition to my collection, {author}! \n"
                            print("CI: ", self.stored_comments[-1])
                            reply(comment, output)
                        elif author in [x["author"] for x in self.stored_comments] and random.random() < 0.01:
                            for x in reversed(self.stored_comments):
                                if x["author"] == author:
                                    comm = x["comment"]
                            output = f"Ah, {author}! I have your comment in my collection! \n" \
                                     f"'{comm}' - (c) {author}"
                            reply(comment, output)
                        elif "see" in comment_text and "collection" in comment_text:
                            comm = self.stored_comments[-1]["comment"]
                            auth = self.stored_comments[-1]["author"]
                            output = f"Ah, {author}! Here's my latest collection item! \n" \
                                     f"'{comm}' - (c) {auth}"
                            reply(comment, output)
                        else:
                            for pattern in self.replies.keys():
                                if pattern.lower() in comment_text.lower():
                                    rep = random.choice(self.replies[pattern]).replace("username", str(author))
                                    reply(comment, rep)
                                    break
            except Exception as e:
                print(f"caught exception {e}, sleeping")
                time.sleep(60)


if __name__ == '__main__':
    lars = Lars()
    grievous = Grievous()
    pr1 = multiprocessing.Process(target=lars.__call__)
    pr2 = multiprocessing.Process(target=grievous.__call__)
    pr1.start()
    pr2.start()
    pr1.join()
    pr2.join()
