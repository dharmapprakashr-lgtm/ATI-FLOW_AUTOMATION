# AtiFlow v2.0 — End-to-End Configuration Guide

**Audience:** Support Team
**Purpose:** Configure AtiFlow from scratch — Admin setup → Execution Source Config → Requester flow → Dispatcher flow → FM trip verification.
**Environment:** `https://192.168.6.32`
**Connected FM:** `192.168.6.12`

---

## How to use this document

- Follow the sections **in order**. Each step depends on the previous one.
- Values shown (e.g. `test_45`, `10001`) are **sample values** used in this walkthrough. Replace them with values that match your site/customer.
- Screenshot placeholders are marked as `![...](images/...)`. Drop the image file into the `images/` folder using the exact filename shown, and it will render automatically.
- Anything marked **Note** is a gotcha that has caused issues before — do not skip it.


## Table of Contents

1. [Login to Admin Portal](#1-login-to-admin-portal)
2. [Create a Processing Area](#2-create-a-processing-area)
3. [Configure the Processing Area](#3-configure-the-processing-area)
   - [3a. Materials](#3a-materials)
   - [3b. Container](#3b-container)
   - [3c. Machine Names](#3c-machine-names)
   - [3d. Station Mapping](#3d-station-mapping)
   - [3e. Staging Area](#3e-staging-area)
   - [3f. Workflow](#3f-workflow)
4. [Execution Source Config](#4-execution-source-config)
   - [4a. Requester Device](#4a-requester-device)
   - [4b. Dispatcher Device](#4b-dispatcher-device)
   - [4c. Supervisor Device](#4c-supervisor-device)
5. [Login as Requester Device](#5-login-as-requester-device)
6. [Login as Dispatcher Device](#6-login-as-dispatcher-device)
7. [FM Verification (Trip Assignment)](#7-fm-verification-trip-assignment)
8. [Changing the FM IP (Admin → Settings)](#8-changing-the-fm-ip-admin--settings)
9. [Quick Reference — Sample Config Sheet](#9-quick-reference--sample-config-sheet)
10. [Troubleshooting Checklist](#10-troubleshooting-checklist)

---

## 1. Login to Admin Portal

**URL:** `https://192.168.6.32`

The login page loads. Sign in with the Admin credentials.

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

> **Note:** Admin is the only role that can create Processing Areas, Materials, Machines, Workflows, and Execution Source devices. Requester / Dispatcher / Supervisor logins are created *later*, in Step 4.
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 09-51-58" src="https://github.com/user-attachments/assets/ed97f996-2948-4e46-b04c-7a2c036bfdc1" />


---

## 2. Create a Processing Area

Navigate to **Processing Area → Create**.

| Field | Sample Value |
|---|---|
| Name | `test_45` |
| Description | `for testing purpose` |

> **Note:** Processing Area name and description are free-text — set them according to your site requirement. This name is auto-inherited later by Materials, Machines, and Station Mapping, so pick something meaningful.

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 09-53-14" src="https://github.com/user-attachments/assets/3d77af44-b501-4cdc-8112-5027c3656f4b" />


---

## 3. Configure the Processing Area

Open the newly created Processing Area (`test_45`) and fill in each sub-section below.

<img width="1652" height="962" alt="image" src="https://github.com/user-attachments/assets/64062cd0-ffaa-431a-9b26-85435d68665c" />


---

### 3a. Materials

Add the material type that will be requested and moved.

| Field | Sample Value |
|---|---|
| Material Type Name | `testing_material_45` |
| Pre-Processing Time (mins) | `1` |
| Max Qty | `23` |
| Staging Area | `Enable` |
| Process Name | *auto-filled* — current Processing Area name (`test_45`) |
| Production Unit | `MFG3_10CFE` |
| Prefix Associated | `DSW` |

> **Note:** `Staging Area = Enable` is mandatory if you want this material to be stored in / picked from a staging area. If it is disabled, staging-based workflows will not pick up this material.

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 09-57-56" src="https://github.com/user-attachments/assets/3c0f1dec-c5db-4f65-9839-182d93ef19e9" />


---

### 3b. Container

Define the physical carrier used to move the material.

| Field | Sample Value |
|---|---|
| Container Type | `Trolly` *(options: Trolly / Pallet / Bin)* |
| Container Sub-type | `mini trolly` |
|Hitch Length  |'45' |
| Dimensions (L\*W\*H) | `232*22*45` |
| Quantity | `1` |

> **Note:** Dimensions must be entered in the `L*W*H` format. Container capacity indirectly limits how much of the material can be dispatched in a single trip.

<img width="1920" height="964" alt="image" src="https://github.com/user-attachments/assets/71697736-2b62-4c4c-811f-03bf83b22744" />


---

### 3c. Machine Names

Two machines are required — one **Consumption** point and one **Production** point.

**Machine 1 — Consumption**

| Field | Sample Value |
|---|---|
| Machine Name | `consuption_machine_45` |
| Point Type | `Consumption Type` |
| Area Name | *auto-filled* — Processing Area name |

**Machine 2 — Production**

| Field | Sample Value |
|---|---|
| Machine Name | `production_machine_45` |
| Point Type | `Production Type` |
| Area Name | *auto-filled* — Processing Area name |

> **Note:** The Requester Device (Step 4a) is bound to a machine. If you only create one machine type, the Requester will not be able to raise both consumption and production style requests.

<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/235318d5-0a41-4466-bd43-56c3fb8548b6" />

<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/e375b3db-f86c-40db-b4ba-19f12a22b267" />



---

### 3d. Station Mapping

Station Mapping links a Material Type to a physical station ID on the map.

> **Note:** Station Mapping is **optional**. If you do not want dynamic mapping, you may keep the configuration **Static** instead.

**Mapping 1 — Pick**

| Field | Sample Value |
|---|---|
| Mapping Name | `pick` |
| Material Type | `testing_material_45` |
| Production Unit | *auto-filled* |
| Station ID | `pick2_gg` |

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-05-40" src="https://github.com/user-attachments/assets/0bdf56ed-8389-4662-8de2-b9b946e0bb26" />


**Mapping 2 — Drop**

| Field | Sample Value |
|---|---|
| Mapping Name | `drop` |
| Material Type | `testing_material_45` |
| Production Unit | *auto-filled* |
| Station ID | `auto2_gg` |

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-06-40" src="https://github.com/user-attachments/assets/f044f972-0de7-48fc-be95-291c323890ab" />


---

### 3e. Staging Area

This screen displays the Staging Area that has been drawn on the **map**, along with the live status of every station inside it.

**Station status colour legend:**

| Colour | Status | Meaning |
|---|---|---|
| 🟢 Green | **Available** | Station is free, can accept material |
| 🟡 Yellow | **Reserved** | Station is held for an active/upcoming request |
| 🔴 Red | **Blocked** | Station is unusable (manual block / fault) |
| 🔵 Sky Blue | **Filled** | Station currently holds material |

From this screen you can also **manage** the Staging Area — e.g. assign a Material to a specific Staging Area station.

> **Note:** If no Staging Area appears here, it has not been created on the map. That is a map-side configuration, not an AtiFlow-side one.

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-09-15" src="https://github.com/user-attachments/assets/834ccef1-7393-4eef-9704-6fc3719d0b23" />


---

### 3f. Workflow

Workflows define *how* material moves. Create workflows as per requirement. In this reference setup, **four** workflows were created to cover all movement combinations.

| # | Workflow Name | Movement |
|---|---|---|
| a | `anyStation_to_StagingArea` | Any station → Staging Area |
| b | `stagingArea_to_any_station` | Staging Area → Any station |
| c | `Order_material_manual` | Material ordered, manual dispatch |
| d | `order_material_auto` | Material ordered, auto dispatch |

<img width="1917" height="1008" alt="image" src="https://github.com/user-attachments/assets/fb940a83-4329-4595-92cc-0dec684bdba3" />


#### a) anyStation_to_StagingArea

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-11-40" src="https://github.com/user-attachments/assets/2ef9822e-09e0-4d0d-b65d-bc06ed317a81" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-11-46" src="https://github.com/user-attachments/assets/69de3498-e149-4f61-b889-903359e1addc" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-11-58" src="https://github.com/user-attachments/assets/2209ed22-70d8-486e-aa61-b4f8c203a869" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-12-11" src="https://github.com/user-attachments/assets/e9655cac-7e43-41c3-8ca7-b66c4616cc09" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-16-23" src="https://github.com/user-attachments/assets/1abdbd2f-16b5-44eb-961f-b2c09efc9758" />





#### b) stagingArea_to_any_station

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-13-29" src="https://github.com/user-attachments/assets/ef7f57fb-05d5-414d-880e-af0c2c35e79c" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-13-42" src="https://github.com/user-attachments/assets/a9ec0f30-bdba-4377-bd5d-8d0451766384" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-13-52" src="https://github.com/user-attachments/assets/21e8164e-c019-4dc2-83a7-7d16e9d85a80" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-14-08" src="https://github.com/user-attachments/assets/b0082d97-0934-4c5b-8cb4-2493cdc028a1" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-16-37" src="https://github.com/user-attachments/assets/96fb74cb-366e-4459-8629-2ade9ab81ed4" />


#### c) Order_material_manual

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-14-31" src="https://github.com/user-attachments/assets/d9dbe90c-5ec6-477b-ade6-babffcb46a1f" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-14-40" src="https://github.com/user-attachments/assets/d3e77bdf-bbb7-47ae-85e9-82740cb0f0b2" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-14-47" src="https://github.com/user-attachments/assets/562e48db-bd83-4832-8f74-997c5315ae95" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-14-59" src="https://github.com/user-attachments/assets/4c991fef-0a1a-4375-aaeb-484296fdc435" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-15-15" src="https://github.com/user-attachments/assets/f9fc92bd-ff01-400c-bf48-bcf0160b73e6" />



#### d) order_material_auto

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-14-31" src="https://github.com/user-attachments/assets/626e622b-ad23-4148-b648-bb536f1fa276" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-15-28" src="https://github.com/user-attachments/assets/c03c60de-047a-4f24-9004-6fc60905b0fc" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-15-37" src="https://github.com/user-attachments/assets/88eabe9c-e849-4a94-a9f0-eb40c5744f30" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-15-50" src="https://github.com/user-attachments/assets/9da38cb6-0d3b-4531-95a1-709648b491d9" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-15-59" src="https://github.com/user-attachments/assets/e25d0808-031c-4b04-a0bb-3e03151e0c75" />


---

## 4. Execution Source Config

Here we create the three device logins: **Requester**, **Dispatcher**, and **Supervisor**.

> **Note (critical):** Device IDs must be **unique across all three roles**. Reusing an ID between Requester / Dispatcher / Supervisor will cause login and routing failures.

---

### 4a. Requester Device

| Field | Sample Value |
|---|---|
| Requester Name | `mohit_requester` |
| Device ID | `10001` |
| Password | `12345` |
| Bound Machine | `consumption_machine_45, MFG3_10CFE` |
| Bound Workflows | `order_material_auto`, `Order_material_manual`, `stagingArea_to_any_station`, `anyStation_to_StagingArea` |
| Visible Staging Area | `AH_Stage` *(as present in the map)* |

> **Note:** Whatever you bind here is exactly what the Requester will see after login. If a workflow is missing from the Requester's dropdown later, it was not bound at this step.

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-32-15" src="https://github.com/user-attachments/assets/30ba0d5d-9486-4ddf-ace9-d50fd8dcf7f3" />


---

### 4b. Dispatcher Device

| Field | Sample Value |
|---|---|
| Dispatcher Name | `mohit_dispatcher` |
| Device ID | `10002` |
| Password | `123456` |
| Bound Stations | `auto2_gg`, `auto1_gg`, `pick2_gg` |
| Visible Staging Area | `AH_Stage` |

> **Note:** The Dispatcher can only act on requests originating from its **bound stations**. If a request never appears in the Dispatcher's Pending tab, check the station binding first.

<img width="1917" height="1008" alt="image" src="https://github.com/user-attachments/assets/73ce9a38-5266-4081-aebf-6e275c49d484" />


---

### 4c. Supervisor Device

| Field | Sample Value |
|---|---|
| Supervisor Name | `mohit_supervisor` |
| Device ID | `10003` |
| Password | `12345` |
| Visible Staging Area | `AH_Stage` |
| Processing Area | `test_45` |

<img width="1917" height="1008" alt="image" src="https://github.com/user-attachments/assets/b30b0049-28aa-4197-a585-1ccad62bbcd4" />


---

## 5. Login as Requester Device

**URL:** `https://192.168.6.32`

| Field | Value |
|---|---|
| User | `mohit_requester` *(as created in Admin portal)* |
| Password | `12345` |

### Post-login verification

Perform these checks **before** raising any request:

- [ ] **a)** Verify the **machine name** in the dropdown matches what was bound in Admin (`consumption_machine_45`).
- [ ] **b)** Verify all **bound workflows** are listed. Select the workflow you want to raise the request against.
- [ ] **c)** Verify the **Staging Area** is visible on screen.

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-47-35" src="https://github.com/user-attachments/assets/297e4ff4-5c1f-4eaa-99b6-b70697a786ed" />


### d) Request status tabs

The Requester screen has **4 sub-tabs** (plus All), showing requests raised from this device:

| Tab | Shows |
|---|---|
| **Requested** | Newly raised, not yet picked up |
| **In Progress** | Currently being executed |
| **Completed** | Successfully finished |
| **Cancelled** | Cancelled / aborted |
| **All** | Everything above combined |

<img width="1917" height="1008" alt="image" src="https://github.com/user-attachments/assets/0aa8a3c5-5304-49a6-a7b2-85651bf46bf9" />


### e) Make a New Request

Click **Make New Request**.

**(i) Request Material tab**

1. Enter the SKU: `DGT15A0666-01`
2. Multiple **sub-SKUs** will be listed — select the **Available** one.
3. Click **`+`** to add the item.
4. Click **Next**.

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-47-49" src="https://github.com/user-attachments/assets/9c8521aa-92d1-49b2-83f6-a8414ab6dabc" />
<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-48-09" src="https://github.com/user-attachments/assets/89be3df1-545e-4935-bdb2-203f85b86378" />


**(ii) Request Summary tab**

The Request Summary tab displays a summary of the requested material — verify quantity, SKU, and destination before proceeding.

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-48-17" src="https://github.com/user-attachments/assets/d0738ec9-7218-4f29-a2d7-a6eb3665d4a9" />


**(iii) Confirm**

Click **Confirm** to submit the request. It will now appear under the **Requested** tab, and simultaneously in the Dispatcher's **Pending** tab.

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 10-48-27" src="https://github.com/user-attachments/assets/e996954d-e533-4d22-a1c7-f33b2b7d5c1c" />


---

## 6. Login as Dispatcher Device

**URL:** `https://192.168.6.32`

| Field | Value |
|---|---|
| User | `mohit_dispatcher` *(as created in Admin portal)* |
| Password | `123456` |

### Post-login verification

- [ ] **a)** Verify the **stations** bound in Admin are visible (`auto2_gg`, `auto1_gg`, `pick2_gg`).

<img width="1919" height="1012" alt="Screenshot from 2026-08-20 11-00-13" src="https://github.com/user-attachments/assets/256253f0-cc25-47e1-a028-f6a8e8267781" />


### b) Dispatcher tabs

Three sub-tabs are available: **Pending**, **Dispatched**, **All**.

Each row displays:

| Column | Description |
|---|---|
| **ID** | Unique request identifier |
| **Request Details** | SKU / material / quantity |
| **Request Time** | Timestamp of the request |
| **Status** | Current state of the request |
| **Decision** | Approve / Not Approve |

<img width="1917" height="1008" alt="image" src="https://github.com/user-attachments/assets/b3b3cded-c94b-4711-9734-0cdc3ba2939b" />


### c) Dispatch the request

Click **Dispatch** on the target request. The request moves from **Pending → Dispatched**, and a trip is raised in the FM.

---

## 7. FM Verification (Trip Assignment)

> **Note (mandatory verification step):** Keep the FM open in a **parallel browser tab** throughout this flow.

**FM URL / IP:** `192.168.6.12` *(currently connected to AtiFlow)*

**Steps:**

1. Open the FM in a parallel tab.
2. Navigate to **Manage Trips**.
3. Observe the trip list **before** dispatching — note the existing trips.
4. Go back to the Dispatcher tab and click **Dispatch**.
5. **Refresh the FM** page.
6. Confirm a **new trip has been assigned** in Manage Trips.

If no trip appears after refresh, the AtiFlow ↔ FM integration is not passing the request through — see the troubleshooting checklist below.

<img width="1917" height="1008" alt="image" src="https://github.com/user-attachments/assets/41bfd87c-0695-4eb8-9536-c4c77c27cf99" />


---
---

## 8. FM Connection Setup (Admin → Settings)

During installation, AtiFlow must be pointed at the FM it will talk to. This is done entirely from the Admin portal — nothing else needs to be re-created.

**Path:** Login as Admin → **Settings** → FM Connection

| Field | What to enter | Sample Value |
|---|---|---|
| **FM IP** | IP address of the FM this AtiFlow instance will connect to. | `192.168.6.12` |
| **Client ID** | Provided by the **development team**. Enter exactly as given. | `atiflow-client-<id>` |
| **Client Secret** | Provided by the **development team**. Enter exactly as given. | `<secret-string>` |

> **Note:** The **Client ID** and **Client Secret** are generated **only once** and are stored in the **plugins**. They are **common across all FMs**. After the first install, if you only need to point AtiFlow at a different FM, change the **FM IP** only — keep Client ID and Client Secret exactly the same.

> ⚠️ **Security note:** Do not paste real Client Secrets into this document, tickets, or chat. Share them only through your team's secure channel.

---

### 8.1 Which path do I follow?

| Situation | Go to |
|---|---|
| Fresh install, credentials provided by dev team | [8.2](#82-fresh-install--first-time-setup) |
| Already installed, only need a different FM | [8.3](#83-switching-to-a-different-fm) |
| No credentials given, or status won't show Connected | [8.4](#84-fallback--when-you-have-no-client-id--client-secret) |

---

### 8.2 Fresh install — first-time setup

1. Login to the Admin portal (`https://<atiflow-server-ip>`) with the Admin credentials.
2. Go to **Settings** → **FM Connection**.
3. Enter the **FM IP** of the client's FM.
4. Enter the **Client ID** and **Client Secret** shared by the development team.
5. Click **Save**.
6. Verify the connection status shows as **Connected**.

- ✅ Status shows **Connected** → setup is done. Stop here.
- ❌ Status does not show **Connected**, or you were never given credentials → go to [8.4](#84-fallback--when-you-have-no-client-id--client-secret).

---

### 8.3 Switching to a different FM

1. Go to **Settings** → **FM Connection**.
2. Replace the **FM IP** only.
3. Do **not** touch Client ID / Client Secret — they are already saved in the plugins.
4. Click **Save**.
5. Verify the connection status shows as **Connected**.

---

### 8.4 Fallback — when you have no Client ID / Client Secret

Normally the **development team provides** these to whoever is deploying AtiFlow. **Always ask them first** — that is the standard path.

Use this fallback **only if**:

- You were never given a Client ID / Client Secret, **or**
- You entered everything correctly but the status still does **not** show **Connected**.

**Order of operations:**

1. Create an **appuser** on the FM → [8.5](#85-creating-an-appuser-on-the-fm)
2. Copy the generated **Client ID** and **Client Secret**
3. Save them into the **MongoDB config** → [8.6](#86-saving-the-credentials-into-mongodb)
4. Re-run the FM configuration
5. Return to Admin → **Settings** and confirm status is **Connected**

> **Important:** Creating a new appuser generates a **fresh** Client ID / Client Secret pair. The old pair stored in the plugins will stop matching. Once you create a new one, make sure the new values are saved in Mongo **and** shared back with the team — otherwise the next deployment will fail.

---

### 8.5 Creating an appuser on the FM

The FM has no UI screen for this. The appuser is created by calling the FM API from its built-in Swagger docs page.

**Prerequisites**

- FM IP reachable from your machine
- **super_admin** credentials on the FM — the create endpoint is restricted to `super_admin` only
- Access to the AtiFlow MongoDB (needed in [8.6](#86-saving-the-credentials-into-mongodb))

> ⚠️ The FM docs are served over plain **HTTP on port 8000**. The Client Secret is returned over this connection, so perform these steps from **inside the client's network only** — never over a public or untrusted link.

**Steps:**

1. Open the FM API docs in a browser:

   ```
   http://<fm-ip>:8000/docs
   ```

   *(example: `http://192.168.6.12:8000/docs`)*

2. Scroll to the **App Users** section.

3. **Authorize as `super_admin` first** — click the 🔒 lock icon on `POST /v1/app_user`, or the **Authorize** button at the top of the page, and log in. Without this, the call returns an authorization error.

4. Expand **`POST /v1/app_user` — Create App User**.

5. Click **Try it out**.

6. Replace the example request body with your values:

   ```json
   {
     "app_user_name": "atiflow",
     "app_user_description": "AtiFlow integration user",
     "allowed_apis": [
       "<api-scope>"
     ],
     "token_expiry_days": 365
   }
   ```

   | Field | What to enter |
   |---|---|
   | `app_user_name` | `atiflow` (or `atiflow-<site-name>` if multiple installs) |
   | `app_user_description` | `AtiFlow integration user` |
   | `allowed_apis` | List of API scopes AtiFlow is allowed to call — *`<confirm exact values with dev team>`* |
   | `token_expiry_days` | `365` (default). Note the expiry date — the token must be regenerated before it lapses. |

7. Click **Execute**.

8. A **201 Successful Response** confirms creation. The response body looks like:

   ```json
   {
     "message": "string",
     "data": "string"
   }
   ```

   The **Client ID** and **Client Secret** are returned in the `data` field.

   > ⚠️ **Copy the Client Secret immediately.** It is returned only in this response and cannot be retrieved again. If you lose it, you must create another appuser.

9. Store both values securely (team password manager / secure channel — **not** in this document).

**If you get a 422 Validation Error:** the request body is malformed or a field value is invalid — most commonly a wrong entry in `allowed_apis`. Check the error detail in the response, fix the body, and re-execute.

**Verify the credentials work before moving on:**

1. Expand **`POST /v1/app_user/login`** (OAuth2 Client Credentials Token Endpoint).
2. Click **Try it out**, enter the new **Client ID** and **Client Secret**.
3. Click **Execute** — a successful response returns an access token, confirming the credentials are valid.

Then continue to [8.6](#86-saving-the-credentials-into-mongodb).

---

### 8.6 Saving the credentials into MongoDB

The FM plugin config is edited through **Mongo Express**, the web-based DB editor on the FM.

**Location of the config document:**

| Item | Value |
|---|---|
| **Mongo Express URL** | `https://<fm-ip>/config_editor/` |
| **Database** | `plugin_config` |
| **Collection** | `plugin_mts_bridge` |
| **Client ID field** | `client_id` |
| **Client Secret field** | `client_secret` |

**Steps:**

1. Open Mongo Express in a browser: `https://<fm-ip>/config_editor/`
   *(example: `https://192.168.6.12/config_editor/`)*
2. Open database **`plugin_config`** → collection **`plugin_mts_bridge`**.
3. Open the plugin config document. It looks like this:

   ```json
   {
     "_id": ObjectId("<document-id>"),
     "activate_plugin": true,
     "mts_core_api_url": "https://192.168.6.32:443",
     "mts_internal_api_token": "",
     "client_id": "",
     "client_secret": ""
   }
   ```

4. Fill in the two fields with the values copied in [8.5](#85-creating-an-appuser-on-the-fm):

   | Field | Value |
   |---|---|
   | `client_id` | Client ID returned by `POST /v1/app_user` |
   | `client_secret` | Client Secret returned by `POST /v1/app_user` |

5. While you are in the document, confirm the other fields are correct:

   | Field | Expected value |
   |---|---|
   | `activate_plugin` | `true` — the plugin will not run if this is `false` |
   | `mts_core_api_url` | `https://<atiflow-server-ip>:443` — the **AtiFlow** server, not the FM |
   | `mts_internal_api_token` | Leave as-is unless the dev team says otherwise |

   > ⚠️ **`mts_core_api_url` points at AtiFlow, `client_id` / `client_secret` come from the FM.** Mixing these two IPs up is the most common mistake here.

6. **Save** the document.
7. Restart the AtiFlow service / container if required — *`<confirm with dev team>`*.
8. Re-run the FM configuration.
9. Go to Admin → **Settings** and confirm status shows **Connected**.

---

### 8.7 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Status not **Connected** after saving FM IP | Wrong FM IP, or FM not reachable from the AtiFlow server | Ping the FM IP from the AtiFlow server; confirm the IP with the client |
| Status not **Connected**, FM IP is correct | Client ID / Secret invalid or not matching this FM setup | Follow [8.4](#84-fallback--when-you-have-no-client-id--client-secret) |
| `401 / 403` on `POST /v1/app_user` | Not logged in as `super_admin` | Authorize via the 🔒 icon before executing |
| `422 Validation Error` on create | Malformed body or invalid `allowed_apis` value | Check response detail, correct the body, re-execute |
| Login endpoint fails with new credentials | Secret mistyped or truncated when copied | Re-copy carefully; if lost, create a new appuser |
| Credentials saved in Mongo but nothing happens | `activate_plugin` is `false` | Set `activate_plugin: true` in `plugin_mts_bridge` |
| Plugin active but AtiFlow never receives calls | `mts_core_api_url` pointing at the wrong host | Must be the **AtiFlow** server (`https://<atiflow-ip>:443`), not the FM |
| Worked before, fails after ~1 year | `token_expiry_days` lapsed | Create a new appuser and update Mongo |

---
<img width="1919" height="1008" alt="Screenshot from 2026-08-21 10-50-08" src="https://github.com/user-attachments/assets/6b9fb329-cfe2-4c3c-8d25-bff76419ddb4" />
<img width="1919" height="1008" alt="image" src="https://github.com/user-attachments/assets/17e21693-4526-4503-a22a-7e453fb1a5b7" />

<img width="1917" height="1008" alt="image" src="https://github.com/user-attachments/assets/06a1294e-aac9-47ce-b9ae-d8ee702644f1" />
<img width="1917" height="1008" alt="image" src="https://github.com/user-attachments/assets/8da5402e-2430-4442-989e-7f39519c434b" />

---
## 9. Quick Reference — Sample Config Sheet

| Item | Value |
|---|---|
| AtiFlow URL | `https://192.168.6.32` |
| FM IP | `192.168.6.12` |
| Admin user / password | `admin` / `admin123` |
| Processing Area | `test_45` |
| Material Type | `testing_material_45` |
| Production Unit | `MFG3_10CFE` |
| Prefix Associated | `DSW` |
| Container | Trolly → mini trolly, `232*22*45`, Qty 1 |
| Consumption Machine | `consuption_machine_45` |
| Production Machine | `production_machine_45` |
| Pick Station | `pick2_gg` |
| Drop Station | `auto2_gg` |
| Staging Area | `AH_Stage` |
| Workflows | `anyStation_to_StagingArea`, `stagingArea_to_any_station`, `Order_material_manual`, `order_material_auto` |
| Requester | `mohit_requester` / ID `10001` / pwd `12345` |
| Dispatcher | `mohit_dispatcher` / ID `10002` / pwd `123456` |
| Supervisor | `mohit_supervisor` / ID `10003` / pwd `12345` |
| Test SKU | `DGT15A0666-01` |

---

## 10. Troubleshooting Checklist

| Symptom | Check |
|---|---|
| Workflow missing in Requester dropdown | Workflow not bound under **Execution Source Config → Requester Device → Bound Workflows** |
| Machine missing in Requester dropdown | **Bound Machine** not set, or machine created under a different Processing Area |
| Staging Area not visible to Requester/Dispatcher | **Visible Staging Area** field empty in the device config, or staging area not drawn on the map |
| Material not usable in a staging workflow | `Staging Area = Enable` was not set on the Material (Step 3a) |
| Request never reaches Dispatcher's Pending tab | Request station is not in the Dispatcher's **Bound Stations** list |
| Device login fails / wrong role loads | Duplicate **Device ID** across Requester / Dispatcher / Supervisor |
| Dispatch clicked but no trip in FM | Verify FM (`192.168.6.12`) is reachable and connected to AtiFlow; refresh **Manage Trips**; check station mapping (Step 3d) points to valid station IDs |
| Staging station shows Red (Blocked) | Station manually blocked or in fault — clear from the Staging Area management screen |
| SKU shows no available sub-SKU | No stock mapped to that SKU, or all sub-SKUs already reserved |

---

*Document version 1.0 — AtiFlow v2.0 configuration reference.*
