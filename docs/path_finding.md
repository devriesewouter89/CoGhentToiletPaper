Idee was startpunt te kiezen, sprong in de tijd maken en een zekere rang behouden. In die range kijken of er matches zijn.

Probleem 1: datums in de stream stonden niet mooi en met vreemde karakters ==> dit opkuisen

Eerste naieve testcase: ervan uitgaan dat er voldoende data is en kijken of ik, met voldoende tussenstappen (= # wc rol velletjes) voldoende afbeeldingen vind op x afstand en met een link tussen elkaar.

- Hoe de link zoeken? Lemmatization vs stemming van geselecteerde kolommen

x afstand: eerst op basis van tijd. Wat bleek: data niet uniform genoeg verspreid en tijd lijkt moeilijke metric.
Oplossing: laat tijd los! sorteren van alle entries op basis van tijd, maar dan gewoon sprong maken in de lijst met iedere keer een specifieke afstand en range. Dit komt ongeveer overeen met rekening te houden met de tijdsdistributie en toch te denken in tijd, maar veel gemakkelijker te implementeren.

Nu hebben we een forward motion die rekening houdt met de distributie ifv de tijd, om een path te vinden moeten we een boomstructuur aanmaken, want het is niet gezegd dat we altijd connecties gaan vinden en af en toe moeten we een tak verlaten en een andere tak uitproberen om tot op het einde te geraken! ==> backward motion