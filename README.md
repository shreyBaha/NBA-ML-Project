# NBA Player evaluation and team fit
The goal of this project is to quantify player profiles through various statistics in order 
to compare them to one another and to predict what players fit best for what teams.
## How are players quantified
I believe in order to best understand each player's role and value we must consider the following:
### Physical Attributes
- Height
- Weight
- Agility
    - Horizontal
    - Vertical
- Jumping
    - Horizontal
    - Vertical
- Speed
- Other measureables (ex. Arm length) 


Some of these are by objective measurements, however for attributes such as agility and jumping must be
evaluated through combine workout data where we deem what workouts translate to practical movements on the court 
and what attribute those movements correlate to. 
### Offensive profile
- Volume
    - FGA/100 pos
    - Usage%
    - Min/G
- Shotchart
    - Shot Zone (ex. Mid-Range)
        - attempts
        - fg%
        - efg%
    - Free throws
        - attempts
        - ft%
- Shot diet
    - General 
        - Shot type (ex. Catch and Shoot 3)
            - attempts
            - efficiency
    - Dribble Shooting
        - Range
            - attempts
            - efficiency 
    - Jump Shooting
        - Contest Range
            - attempts
            - efficiency
    - Possesion shooting
        - Time with ball
            - attempts 
            - efficiency 
- Playmaking/Reliability 
    - Assist Share
    - TOV%
    - USG%
    - AST
    - TOV


There is a lot of good data available through the nba_api in regards to shot volume, location, type, and efficiency. Through this data we can effectively map player's roles and value in regards to their shooting. Unfortunately there is a lack of passing data so we must make do with some more basic stats to quantify playmaking. Unfortunetly this will lead to a lack of context to the sheer totals not properly allowing us to understand how those totals are generated which can help us infer player roles. 
