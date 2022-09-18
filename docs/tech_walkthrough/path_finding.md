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

Nu wordt alles wel heel traag (serieel alle uri's opvragen), 