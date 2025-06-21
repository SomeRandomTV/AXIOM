# The Command Handler

This is where all prep is done to an input command. \
For example, if you said "get weather for Austin" \
It would be parsed into:  
- `/get`  
- `weather`  
- `for`  
- `Austin`

Calling the `get_weather()` function with the `Austin` parameter.


For now there are only four types of commands:  
- `/get` &rarr; get data
- `/create`  &rarr; create data
- `/schedule`  &rarr; schedule an event 
- `/notify`  &rarr; send a message 

Notice, all commands start with `"/"`  

At the very top level this is the command structure:\
/`<cmd>` `<cmd_body>`

Where: 

- `<cmd>` : the command to be called (e.g. `get`, `create`, `schedule`, `notify`)  
- `<cmd_body>` : the parameters for the command (e.g. `<Austin>`) 

> **Data schema for all created objects**  
> ```json
> {
>  "function call": "<function_name>",
>  "target": "<additional params>"
> }

---

## /get

This is a _fetch_ command; it retrieves data from whatever source you specify.

**Syntax** \
/get `<function>` for `<target>`


- `/get` : command  
- `<function>` : the function to be called (e.g. `weather`, `news`, `stock`)  
- `for` : delimiter before parameters  
- `<target>` : target location, topic, etc.

> **Example usage**  
> ```
> /create get weather for Austin
> ```
> _Returns:_  
> ```json
> {
>   "function_call" : "get_weather()",
>   "target": "Austin"
>  }

---

## /create

Creates new user‐type objects (residents, staff, visitors, emergency services).

**Syntax** \
/create `<type>` `<params>`


- `/create` : command  
- `<type>` : one of `resident`, `staff`, `visitor`, `EmergencyServices`  
- `<params>` : attributes for the object

**Supported types & params**  
- **resident**  
  - `name`:  `<first>  <last>`  
  - `height`:  `<ft>  <in>`  
  - `weight`: `<lbs>`  
- **staff**  
  - `name`: `<first> <last>`  
  - `height`: `<ft> <in>`  
  - `weight`: `<lbs>` (_optional_)  
  - `temp`: `<true|false>` (_temporary flag_)  
- **visitor**  
  - `name`: `<first> <last>`  
  - `purpose`: `<reason for being here>`  
- **EmergencyServices**  
  - `type`: `<fire dept|police|ems>`
  - `severity`:`<critical|high|medium|low>`

> **Example usage**  
> ```
> /create resident Smith Jerry height 6 4 weight 120
> ```
> _Returns:_  
> ```json
> {
>   "function_call" : "create_user",
>   "target": {
>     "name": "Jerry Smith",
>     "type": "resident",
>       "any": {
>         "height": "6'4\"",
>         "weight": "120 lbs"
>      }
>    }
>  }
> ```

---

## /schedule

Creates an event at a specified date and time.  
_(Date parameters to be defined in future iterations.)_

**Syntax** \
/schedule <`user`> for <`event`> at <`time`>

**Example Usage**
> **Example usage**  
> ```
> /schedule jerry for Dentist at 10pm
> ```
> _Returns:_  
> ```json
> {
>   "function_call" : "schedule",
>   "target": {
>     "user": "Jerry Smith",
>     "event": "Dentist",
>     "time": "10pm"
>    }
>  }
> ```

---

## /notify

This command notifies or sends a message to a recipient 

**Syntax** \
/notify `<recipient>` `<message>`

**Example Usage**
> **Example usage**  
> ```
> /schedule notify Morty Dentist tomorrow at 10am
> ```
> _Returns:_  
> ```json
> {
>   "function_call" : "notify_user",
>   "target": {
>     "recipient": "Jerry",
>     "message":  "Dentist tomorrow at 10am"
>    }
>  }
> ```


## Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant H as CommandHandler
    participant R as Regex
    participant F as FunctionHandler
    participant L as LLM

    U->>H: set_command(raw_command)
    H->>R: MASTER_SPLITTER.match(raw_command)
    alt slash-style command
        R-->>H: match found
        H->>H: cmd = match.group(cmd)
        H->>H: rest = match.group(rest)
    else no slash prefix
        R-->>H: no match
        H->>H: rest = raw_command
    end

    U->>H: parse_command()
    alt cmd == get
        H->>R: GET_CMD_PATTERN.match(rest)
        alt match success
            R-->>H: match object
            H->>H: validate function name
            H->>H: set function_call
            H->>H: set target
            H->>H: set function_flag to 1
        else match failure
            H-->>U: ValueError: usage get
        end
    else cmd == create
        H->>R: CREATE_CMD_PATTERN.match(rest)
        alt match success
            R-->>H: match object
            H->>H: extract type and payload
            H->>H: parse key/value pairs
            H->>H: set function_call to create
            H->>H: set target params
            H->>H: set function_flag to 1
        else match failure
            H-->>U: ValueError: usage create
        end
    else cmd == schedule
        H->>R: SCHEDULE_CMD_PATTERN.match(rest)
        alt match success
            R-->>H: match object
            H->>H: set function_call to schedule
            H->>H: set target params
            H->>H: set function_flag to 1
        else match failure
            H-->>U: ValueError: usage schedule
        end
    else cmd == notify
        H->>R: NOTIFY_PAYLOAD.match(rest)
        alt match success
            R-->>H: match object
            H->>H: set function_call to notify
            H->>H: set target params
            H->>H: set function_flag to 1
        else match failure
            H-->>U: ValueError: usage notify
        end
    else
        H->>H: function_flag remains 0
    end

    U->>H: dispatch()
    alt function_flag == 1
        H->>F: call function_call with target
        F-->>H: result data
        H->>U: return function result
    else
        H->>L: send prompt(rest)
        L-->>H: response text
        H->>U: return LLM response
    end

    U->>H: get_command()
    H-->>U: { function_call, target }

```




Something
