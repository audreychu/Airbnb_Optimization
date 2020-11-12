# Airbnb_Optimization
### DS-GA 1001 Project

### Team members, netid
- Abbas Dawood, da2729
- Audrey Chu, ac8839
- Faizan Kanji, fnk9850
- Connor Reed, cr3221

## Domain and business question
**What:** 
- Predicting prices, ratings, and/or booking frequencies of Airbnb rental listings in [some subset of] major cities using listing, geospatial, and time series data
- Airbnb data: http://insideairbnb.com/get-the-data.html 

**Why:** 
- Improve recommendations made to customers seeking to travel at some point in the future with a given budget (and destination)
- Help hosts more appropriately price their listings to improve revenue

## Potential approaches

**‘Macrogeographic’ approach:** 
- Evaluating temporal dynamics of rental behaviors across different cities/tourist destinations
- Value: Consumers can benefit from predicting price surges in tourism destinations, create a “best time to book” prediction based on date and destination (hopper for Airbnb)

**‘Microgeographic’ approach:** 
- Engineering features from hyper-localized geospatial data such as congestion or mobility metrics (via Uber Movements data), localized demographic data and distance to points of interest
- Focus will be on 1 or a few cities
- Value: Helpful for hosts in a couple of ways
  - If hosts have multiple real estate properties in a region, help them determine appropriate localized pricing / make decisions fon whether to put a property on airbnb or not
  - Help hosts understand what baseline price should be based on “uncontrollable” factors of a neighborhood/microgeography (e.g. traffic, demographics, etc.) and how to mark-up “controllable” factors (e.g. amenities, cancellation policies, etc.)

**Causal analysis of major/exogenous events:**
- Exploring the causal influence of larger events (e.g., COVID-19, cultural events such as Mardi Gras, natural disasters) on target variable (i.e., price, rating, booking frequency) and how those influences might interact with or be mediated by other features of a given listing
- In this case our supervised learning problem would either focus on predicting a valid counterfactual/generating a synthetic control group to measure incrementality or predicting incrementality
- Value: Could help hosts maximize profits from holiday tourism or help hosts adapt to adversely disruptive events



