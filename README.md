# Final Project Plan

(Just write your [Plan](https://w3.cs.jmu.edu/cs347/f26/project/plan/) right here in this README. You can edit this file however you like.)

## Sketch
<img width="2454" height="1633" alt="IMG_1935" src="https://github.com/user-attachments/assets/62a1e82c-2c91-4202-a4e7-afdd610bfdaa" />
<img width="3024" height="2004" alt="IMG_1937" src="https://github.com/user-attachments/assets/0316de2c-eb17-4b33-91a7-198349d8b5a4" />
<img width="3024" height="1713" alt="IMG_1936" src="https://github.com/user-attachments/assets/5b17ad8e-e23c-4ec9-98a8-71d6d5ec4845" />

## Narrative

Your **project narrative** must begin with the project title, your team name, and the student names, and include the following sections (about 200 words each):

### Purpose
The purpose of the application is to provide an interactive location-based interface that can display historical maps of a user's current environment from any time available. The app will be able to show how user’s environments have changed through time. Many people walk through culturally rich and historically significant areas every day without realizing the history around them. Textbooks and maps are disconnected to what you see when you are actually in that space. This application solves that problem by bridging the gap between the past and the present through a mobile interface. By leveraging modern GPS technology and a database of historical maps/satellite imagery, we will be able to overlay historical maps (possibly with unsupervised geo-referencing) directly onto a user's current physical position; the app creates a visceral, immersive educational experience. Our app will make it easy to explore the history of any location within our database and it will help to keep the history of local areas from being forgotten.
### Users
The primary demographic of this application encompasses a large group. This will include tourists, history enthusiasts, and teachers. Tourists and history buffs frequently travel to new destinations in order to better understand an area’s heritage and culture, but some places lack accessibility and resources that contextualize the space/area around them. On the other hand, educators need interactive and tangible tools to make learning history more engaging for students. This application will greatly benefit these users by transforming passive map navigation into an active exploratory experience. The secondary demographic is simple enough where its just anyone else who is slightly curious about the environment around them. This could be anyone just simply interested in seeing a historical view of their hometown, whether by walking around or by car as a substitute for Google Maps. For tourists, the application can serve as an interactive pocket guide while they are walking around a town/city they are visiting. For teachers and their students, it can provide a highly visual contextual way to view local history. Also, businesses interested in this technology solution like museums, national parks, etc would be another long-term user later down the line. Overall, this can provide people with a way to be aware of their surroundings in a historical context without requiring a physical book or map.
### Features
The core functionality of the application centers on real-time location tracking paired with dynamic image overlays. As a user walks through a specific area, the app uses the mobile device's GPS to pinpoint their exact coordinates. The user can choose to overlay historical maps based on their location. The historical map will then be stretched over the original map showing the user what the location used to look like in the past. This feature includes a list of dates to show different time periods, so a user can pick the exact time in history that they want to see. There will be Points of Interest (POIs) that allow the user to get more information of the location they are in. For example they would be able to click on a famous building to see pictures of that building and have information that they can read about the POI. A comparison tool will also be available to show the differences between the historical map and the current map. This feature shows the side-by-side views of the two different maps, so the user will be able to easily see the changes. One example of the app being used was a person standing in downtown Harrisonburg. They open the app and get a prompt asking for what year they would like the map to be changed to. They select the year 1885 the map then gets replaced with the historical map from that time. Their location is marked with a blue dot, and as they walk around downtown the blue dot moves on the dirt roads showing their location on the historical map. They are able to compare the old architecture with the current architecture that they visually see around them. They reach a build that is a POI and are able to click it on the map which shows them pictures and information on the building.
### Data
The application will require reading from a large database in order to manage the information presented to the user. We need to be able to grab data for all of the POIs as well as relevant map data. Users will be able to create account profiles, read historical map data and POI descriptions, update their saved routes or favorite locations, and delete their accounts or saved preferences.
The primary objects, properties, and data types include:
User: ID (Integer, Primary Key), Username (String), Email (String), PasswordHash (String).
MapOverlay: ID (Integer, Primary Key), Year (Integer), ImageURL (String), TopLeftLat (Float), TopLeftLong (Float), BottomRightLat (Float), BottomRightLong (Float).
PointOfInterest (POI): ID (Integer, Primary Key), Title (String), Description (Text), Latitude (Float), Longitude (Float), MapID (Integer, Foreign Key).
An example of representative data would be a MapOverlay record with Year: 1885, ImageURL: "harrisonburg_1885.png", and its corresponding geospatial boundary coordinates. The intended relationships between these objects include a one-to-many relationship between a MapOverlay and PointOfInterest (one map can contain many POIs), and a many-to-many relationship between User and PointOfInterest to allow users to favorite multiple historical sites.

## Claims

Draft your expectation of which [claims](./claims.md) you will make for your project

Intermediates:
1. I50 - user input
2. I60 - data import/export
3. I70 - integrates external API
4. I80 - provides its own API
5. I90 - mobile responsiveness
6. I170 - language translation
7. I10 (maybe) - handles file uploads
8. I20 - search functionality
9. I89 - accessbility
10. I150 - bulk operations (perform actions on multiple records at once)
11. I100

References are optional, but you may include "Works Cited" if that simplifies the explanation.
