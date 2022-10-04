Idee was startpunt te kiezen, sprong in de tijd maken en een zekere rang behouden. In die range kijken of er matches zijn.

Probleem 1: datums in de stream stonden niet mooi en met vreemde karakters ==> dit opkuisen
```python
def convert_column_first_year_via_regex(self):  
    """  
    convert_column_first_year_via_regex is a function that formats the "converted_creation_date" column in the pd dataframe to something readable    
    """    
    res = self.df[self.time_col].str.extract(r"([\d+]{4})").squeeze()  
    self.df.insert(10, self.clean_time_col, pd.to_numeric(res), True)
```

Eerste naieve testcase: ervan uitgaan dat er voldoende data is en kijken of ik, met voldoende tussenstappen (= # wc rol velletjes) voldoende afbeeldingen vind op x afstand en met een link tussen elkaar.

- Hoe de link zoeken? Lemmatization vs stemming van geselecteerde kolommen

%%todo: zet tekening van voorbeeld erbij (print statement)%%
x afstand: eerst op basis van tijd. Wat bleek: data niet uniform genoeg verspreid en tijd lijkt moeilijke metric.
Oplossing: laat tijd los! sorteren van alle entries op basis van tijd, maar dan gewoon sprong maken in de lijst met iedere keer een specifieke afstand en range. Dit komt ongeveer overeen met rekening te houden met de tijdsdistributie en toch te denken in tijd, maar veel gemakkelijker te implementeren.

van

```python
def find_indices_in_time_range(self, origin_year: int, time_distance: int, time_spread: int) -> (bool, list[int]):  
    new_origin = origin_year + time_distance  
    new_time_range = [new_origin - time_spread,  
                      new_origin + time_spread]  
    bool_array = self.df.index[  
        (new_time_range[0] <= self.df[self.clean_time_col]) & (self.df[self.clean_time_col] <= new_time_range[1])]  
    if len(bool_array) > 0:  
        res = bool_array.values.tolist()  
        res_bool = True  
    else:  
        res = None  
        res_bool = False  
    return res_bool, res
```
waar we in tijdstappen dachten naar:
```python
def 
```


Nu hebben we een forward motion die rekening houdt met de distributie ifv de tijd, om een path te vinden moeten we een boomstructuur aanmaken, want het is niet gezegd dat we altijd connecties gaan vinden en af en toe moeten we een tak verlaten en een andere tak uitproberen om tot op het einde te geraken! ==> backward motion


Afbeeldingen: de link downloaden: blijkt bij relatief wat afbeeldingen krijg ik geen afbeelding?

```python 
def get_image_uri(self, img_id) -> str:  
    iiif_manifest = "https://api.collectie.gent/iiif/presentation/v2/manifest/{}:{}".format(self.institute, img_id)  
    try:  
        response = urlopen(iiif_manifest)  
    except ValueError:  
        print('no image found')  
    except HTTPError:  
        print('no image found')  
    else:  
        data_json = json.loads(response.read())  
        image_uri = data_json["sequences"][0]['canvases'][0]["images"][0]["resource"]["@id"]  
        return image_uri
def get_image_list_from_tree(self):  
    # we pick the rows from our dataframe which were chose  
    index_list = self.df_tree[self.df_tree["chosen"] == True].index  
    # based on these indexes we pick the data from within our original dataframe  
    df_list = self.df.iloc[self.df.index.isin(index_list)]  
    # we make a list of the objectnumbers, as they are needed to retrieve images  
    object_id_list = df_list["objectnumber"].values  
    img_list = list(map(lambda x: self.get_image_uri(x), object_id_list))  
    for i in img_list:  
        print(i)  
    print(len(img_list))
```
Got me on a random occasion only 12 out of 50 results. Not good...

Plan van aanpak: bij het bouwen van de tree reeds rekening houden met het resultaat van get_image_uri!

Nu wordt alles wel heel traag (serieel alle uri's opvragen), dus gaan we threaded werken!

Van 
```python
def find_overlap_in_series(self, origin, indexes) -> (bool, list[dict]):  
    """  
    @rtype: object  
    @param origin:    @param indexes:    """  
    print("origin:")  
    print(self.df_row(origin))  
    res = list()  
    res_found = False  
  
    for i in indexes:  
        if i == origin:  
            continue  
        # print(self.df_row(i))  
        overlap_found, overlap_list, img_uri = self.find_overlap(origin, i)  
        if overlap_found:  
            print(Fore.GREEN)  
            print(overlap_list)  
            res.append({"index": i, "res": overlap_list, "img_uri": img_uri})  
            res_found = True  
        else:  
            # print(Fore.RED + "nothing found")  
            continue  
        print(Style.RESET_ALL)  
    return res_found, res
```

Naar threaded:

```python

def find_overlap_threaded_in_series(self, origin, indexes) -> (bool, list[dict], list[str]):  
    """  
    TODO not satisfied with this, not functionally written!  
    @rtype: object  
    @param origin: the index in the original dataframe for which we're looking for childs in <indexes> with a textual overlap    @param indexes: the indexes of possible children    """  
    print("origin:")  
    print(self.df_row(origin))  
    res = list()  
    res_found = False  
  
    # we'll multithread the find_overlap function to speed things up  
    que = Queue()  
    threads_list = list()  
    for i in indexes:  
        if i == origin:  
            continue  
        t = Thread(target=lambda q, arg1, arg2: q.put(self.find_overlap(arg1, arg2)), args=(que, origin, i))  
        t.start()  
        threads_list.append(t)  
    for t in threads_list:  
        t.join()  
    while not que.empty():  
        overlap_found, overlap_list, img_uri, index = que.get()  
        if overlap_found:  
            print(Fore.GREEN)  
            print(overlap_list)  
            res.append({"index": index, "res": overlap_list, "img_uri": img_uri})  
            res_found = True  
        else:  
            # print(Fore.RED + "nothing found")  
            continue  
        print(Style.RESET_ALL)  
    return res_found, res
```


Now, my algorithm is basically:
- You have a startnode
- Find all indices we want to evaluate
- Find all childs based on the indices which have a textual overlap with our startnode
- choose one of them as a new startnode
	- If no child nodes are to be found, switch the new startnode

As this takes a long time, perhaps it's faster for future reference to NOT choose the new startnode, yet search childs with overlaps for all nested childs. This implicates:
- more memory usage
- small rewriting part (not choosing one branch + keeping track of the parent)
- if the database is renewed, entire process needs to be redone.


So I've rewritten my flow for easier reuse:
- instead of finding a unique path and only saving this path towards the end
- I build the entire tree structure
- and find a possible path afterwards
- This way making it possible to recuperate the builded tree structure.
As I only keep a link to the images, I don't have this huge memory bounty.

Now, after having some hassles rewriting the code in threads. It takes a **long** time to make the tree structure. That made me think that I check often for the same entry if there's an image present as they appear in different branches. Thus, I'll rewrite the code again to add the uri, if available, to the original dataframe. Then I don't need to have so many requests (which is the bottleneck, together with my sense of patience)

I now preprocess the data to first go through all images and find their URI, if there's none I don't keep them. 
My initial plan was to process all data into a tree, yet after running an entire night I came to next conclusion: it's becoming way to large and slow. I need 50 layers, by morning I had 9 (with 1000 threads in parallel, and a spread of 3):

- layer 1: 1 id to check @ 22:25:34
- layer 2: 5 ids to check
- layer 3: 30 ids to check
- layer 4: 150 ids to check
- layer 5: 738 ids to check
- layer 6: 3947
- layer 7: 19849
- layer 8: 94446
- layer 9: 444545  (400000 @ 08:35:35) ==> I'm not that patient!

each 1000 threads took approx 2 minutes at layer 9. Perhaps my dataframe is becoming too large to be efficient... At layer 8 it was about 20 seconds...