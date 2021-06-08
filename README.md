# COVID-19-Optimal-Resource-Allocation_and_Request-Classification
A solution developed to map essential COVID-19 Relief resources to the needy across a city in the most cost-optimal way, and also to classify incoming SOS messages from those in need of help, for organizational and lesser response times.


## Capabilities
1. __Optimal Resource allocation : --__
   This functionality was designed to ingest dataset provided by the government containing the following data :
    * Available COVID-19 sanitary resources like - Hand sanitizers, Face masks, Gloves, Face Shields etc.
    * Emergency medical resources like COVID-19 hospital beds, Oxygen Tanks, etc. 
    * Available donations of dry ration items for COVID-relief like - Rice, lentils, vegetables, spices etc.
    * Quantity of Supply and Demand of the above resources across the city
    * The name of the locality/business/firm/entity where the above supply/demand is found, locatable on Google Maps.
   
   The tool then attaches a geographical tag (latitude and longitude) to each location. Then it builds a graph network with each location as a node and a supply/demand value associated with each. The cost of each edge is obtained from a configurable distance matrix as required. After the previous steps, the tool suggests a list of optimal resource transfers (according to their specific item category) to minimize the gap between demand and supply with the the following fields :
   * From Location
   * To Location
   * Quantity of Transfer
   * Cost of Transfer

   *This boils down to a LP (Linear Programming) problem and can be posed in the standard form.* 

2. __Automatic SOS Text Classification__

  During the COVID-19 pandemic, the end-users are given a free-text field to write and submit their grievances, medical emergencies and relief requests to the state government. This data is collected, pre-processed and each request is classified to one or more of the following configurable categories :
  * Travel
  * Food
  * Medical
  * Donations
  * Others etc.

   This classified list of citizen SOS requests lets the government authorities re-route the requests to the relevant departments to address them with minimal response time. 
   
   *Here, we use state-of-the-art NLP, Sequence encoding and Deep Learning Techniques to achieve the fucntionality*
   
   
  
