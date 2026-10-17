# CampusVolt API: Design

## 1. Requirements

### Functional
- 1. There will be dashboard which will include six different features for the user which are AI Forecast,Bill Estimator, comparison, History, Analytics and Live Monitor. The API serves the data for these features; the dashboard that displays them is built separately.
- 2. The first feature is AI Forecast which will allow the user to predict the future power consumption, peak power prediction of the day and energy consumption of the particular building. The user has to provide the necessary details like the date and the time for the future power consumption and energy consumption. For peak Power prediction the user will only has to provide a particular date. The response for the future power consumption prediction for a particular time and date will contain the value of power in KW. (Peak power is also in kW; energy consumption is in kWh.) If the date is invalid or the building has too little history, the API returns a clear error and no prediction. [confirm]
- 3. The second feature is Bill Estimator which will allow the user to predict the Bill of electricity beforehand by predicting the energy consumption by using the previous data. For this the User will have to provide the particular month as a input.The application will provide the amount of rupees as a Bill.It will also suggest some optimization rules for the building which will lead to the savings of the user and provides with the total amount of the money saved after optimization
- 4. For the readings: The readings will be taken by the meter in every 5 min(For now to achieve this we will require sensors ) but to achieve this and provide a software application or prototype we can built a simulator which we genrate the values in every 5 min for each meter. The simulator sends its readings to the API, either one at a time or in batches. A reading sent twice for the same meter and timestamp is stored only once. [confirm]
- 5. Comparison, History and Analytics: a user can request a building's energy consumption and cost for a time range (the last six months, the previous month of the same year, or the last month). The API returns the data and the frontend draws the charts. [confirm]
- 6. Live Monitor: the system flags a reading as an anomaly, and a user can list the anomalies for their building. [confirm]
- 7. A user can read data only for their own building and its meter. A request for another building's data is rejected.

### Non-functional
- Latency: p95 under 300 ms when reading stored data; p95 under 2 seconds for a forecast (the model is loaded once at startup). [confirm]
- Availability: 99% over a month, which allows about 432 minutes (7.2 hours) of downtime. 100% cannot be promised by any system. [confirm]
- Durability: once the API confirms a reading is stored, it survives a restart or crash. (Met from Week 2, when PostgreSQL replaces the in-memory store.)
- Consistency: after a reading is accepted, the next query for that building includes it immediately. [confirm]

### Model quality
- The prediction about the energy consumption, power consumption, bill estimator are about 92% accuarte (The machine learning model is accurate about 92%). Metric and test data to be stated: 92% of what, measured how. [confirm]

### Scale
- 1. Users will be the authoried person for a particular Building (Consider there are 6 Buildings so there will be 6 authorized Users). No authrized user can access the information of other building and meter id
- 2. Buildings : There are 6 Buildings and each building has a unique building id which are : B001,B002,B003,B004,B005,B006
- 3. Meters : There are 6 Meters. Each building has its own Meter and each meter has a unique id: M001,M002,M003,M004,M005,M006
- 4. Readings: Each meter is responsible to take a reading every 5 min , so each meter produces almost produces 288 readings per day which makes the total reading to 1728 for 6 meters .
- 5. Requests per second (1 day is about 100,000 s):
  - One request per reading: 288 ÷ 100,000 = 0.00288 req/s per meter; 1,728 ÷ 100,000 = 0.01728 req/s for all 6 (about one request every 58 seconds).
  - One batch per meter per hour: 24 batches per meter per day, 144 per day in total; 144 ÷ 100,000 = 0.00144 req/s.
  - Peak at 5x average: about 0.09 req/s (single readings) or 0.007 req/s (batches). If all 6 meters send at the top of the hour, 6 requests arrive in the same second.
  - Dashboard reads (assuming each of the 6 users makes 20 requests a day): 120 ÷ 100,000 = 0.0012 req/s.
- Conclusion: even at peak this is far below one request per second, so one small server and one database are enough.

### Out of scope
- 1. This is the extension of the feature bill estimator we can provide the user with different options to calculate the bill (for example for government colleges the price of 1 unit of electricity is less by 0.50 paise)
- 2. The dashboard user interface itself. [confirm]
- 3. Pushing notifications to users. Clients fetch anomalies by request. [confirm]

## 2. API design

### Error format (used by every endpoint)
(Write the one JSON shape every error will use.)

## 2. API design

### Error format (used by every endpoint)
{ "error": { "code": "BUILDING_NOT_FOUND", "message": "No building with id B007." } }

### Endpoints

| # | Method | Path | Who can call | Client sends | Response (success) | Errors | Idempotent? |
|---|--------|------|--------------|--------------|--------------------|--------|-------------|
| 1 | POST | `/v1/buildings` | Admin | Body: `building_id`, `name` | `201` the new building | 401; 403 not admin; 409 id already exists; 422 invalid field | No |
| 2 | GET | `/v1/buildings` | Admin (all) or Viewer (own only) | Query: `page`, `limit` | `200` paginated list of buildings | 401; 422 bad page/limit | Yes |
| 3 | GET | `/v1/buildings/{building_id}` | Admin or that building's Viewer | Path: `building_id` | `200` one building | 401; 403 not their building; 404 no such building | Yes |
| 4 | POST | `/v1/buildings/{building_id}/meters` | Admin | Body: `meter_id` | `201` the new meter | 401; 403; 404 no such building; 409 meter id exists; 422 | No |
| 5 | GET | `/v1/buildings/{building_id}/meters` | Admin or that Viewer | Path: `building_id` | `200` list of meters | 401; 403; 404 | Yes |
| 6 | POST | `/v1/meters/{meter_id}/readings` | Simulator or Admin | Body: list of `{timestamp, power_kw}` (max 288) | `201` `{stored: n, duplicates_ignored: m}` | 401; 403; 404 no such meter; 409 same meter and timestamp but a different value; 422 invalid timestamp or value | Yes, by design (duplicates ignored) |
| 7 | GET | `/v1/buildings/{building_id}/readings` | Admin or that Viewer | Query: `from`, `to`, `page`, `limit` | `200` paginated readings, oldest first | 401; 403; 404; 422 (`from` after `to`, bad date) | Yes |
| 8 | GET | `/v1/buildings/{building_id}/consumption` | Admin or that Viewer | Query: `from`, `to`, `granularity` (`day` or `month`) | `200` list of `{period, energy_kwh, cost_rupees}` | 401; 403; 404; 422 | Yes |
| 9 | GET | `/v1/buildings/{building_id}/forecasts/power` | Admin or that Viewer | Query: `at` (date and time in the future) | `200` `{building_id, at, power_kw}` | 401; 403; 404; 409 too little history; 422 bad or past date | Yes |
| 10 | GET | `/v1/buildings/{building_id}/forecasts/peak` | Admin or that Viewer | Query: `date` | `200` `{date, peak_power_kw, expected_at}` | 401; 403; 404; 409; 422 | Yes |
| 11 | GET | `/v1/buildings/{building_id}/forecasts/energy` | Admin or that Viewer | Query: `from`, `to` | `200` `{from, to, energy_kwh}` | 401; 403; 404; 409; 422 | Yes |
| 12 | GET | `/v1/buildings/{building_id}/bill-estimates` | Admin or that Viewer | Query: `month` (YYYY-MM) | `200` `{month, energy_kwh, bill_rupees, suggestions[], savings_rupees}` | 401; 403; 404; 409; 422 | Yes |
| 13 | GET | `/v1/buildings/{building_id}/anomalies` | Admin or that Viewer | Query: `from`, `to`, `page`, `limit` | `200` paginated `{meter_id, timestamp, power_kw}` | 401; 403; 404; 422 | Yes |
| 14 | GET | `/v1/health` | Anyone (no token) | none | `200` `{status: "ok"}` | none | Yes |

### Decisions
(see the list in my reply: confirm or change each one)