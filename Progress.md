![image-20250708190934861](images\image-1.png)

## To do list 7.9:

- add function: Code intepreter . Let users ask math questions or code questions, and then it generates the correct answer or code files, code image using **code_interpreter** tool
- Make the layout.html better, and seperate the QUERY function aside, newly build a query.html, layout.html includes only the Navbar.

## To do list 7.10: 

- function call: Send emails using human languages
- Codex
- Walfram
- **Issue: Mardown in history.html can't be parsed.**

![image-20250711194141867](images\image-2.png)

## Completion 7.10

1. image and file(pdf) inputs

2. Generate images

   **Price**:

   For one 1024*1024 image **input**, it takes about 1024 mutiplies 2.5 tokens , about 2500 tokens to analyse(using gpt-4.1-nano)

   For **output**, see the follows:

   *Likely if I generate one image: 272 / 1 000 000 × $40 ≈ **$0.0109**, I'll spend 0.01$*

   | Quality | Square (1024×1024) | Portrait (1024×1536) | Landscape (1536×1024) |
   | :------ | :----------------- | :------------------- | :-------------------- |
   | Low     | 272 tokens         | 408 tokens           | 400 tokens            |
   | Medium  | 1056 tokens        | 1584 tokens          | 1568 tokens           |
   | High    | 4160 tokens        | 6240 tokens          | 6208 tokens           |

   | Model                  |  Input | Cached input | Output |
   | :--------------------- | -----: | -----------: | -----: |
   | gpt-image-1gpt-image-1 | $10.00 |        $2.50 | $40.00 |

| gpt-4.1gpt-4.1-2025-04-14           | $2.00 | $0.50  | $8.00 |
| :---------------------------------- | ----- | ------ | ----- |
| gpt-4.1-minigpt-4.1-mini-2025-04-14 | $0.40 | $0.10  | $1.60 |
| gpt-4.1-nanogpt-4.1-nano-2025-04-14 | $0.10 | $0.025 | $0.40 |

![image-20250711224726704](images\image-3.png)

3. History successfully allow all the previous image and text![image-20250712003827306](images\image-4.png)

## 7.13 Completion

1. Add web search function. Users can choose it to get the latest news.

2. Optimise the image generation conversation. Now the Image conversation can show users all the messages about the image they generate.

3. History.html adds the picture pharsing function. Now all the pictures in history can be presented correctly.

   ![image-20250713004938939](images\image-5.png)

![image-20250713005008307](images\image-6.png)

**Issue: Markdown still can not be pharsed in history.html**

## 7.14 Completion

1. **FIX ISSUE !! Markdown now can be correctly pharsed in history.html**

![image-20250714141241844](images\image-7.png)

2. Add one function : Code interpreter

   ![image-20250715015153759](images\image-8.png)

It can receive almost every type of files, and generate files you want. 

## 7.15 Test Code Intepreter

![image-20250715180419609](images\image-9.png)

![cfile_68767ae299448191892a3e93ec28fa33](images\cfile_1.png)![cfile_68767ae29a1481919ce35cb52a0c3d0b](images\cfile_2.png)

## 7.19

Finally finish the project. Although there is some pity , like some functions are not realized, I am totally happy about what I made within just two weeks. It's time to show my project.

- **Image generation and memory:**

![image-20250719211653896](images\image-10.png)

- **Simple Texts Generation and Memory:**

![image-20250719211856081](images\image-11.png)

- **Web Search Tool: **

![image-20250719211927671](images\image-12.png)

- **Reasoning Tool (And Web Search Tool)**

![image-20250719212128914](images\image-13.png)

- **Image Explanation**

![image-20250719212214747](images\image-14.png)

- **Code Interpreter**

![image-20250719212352508](images\image-15.png)

![cfile_687bf0989064819189a042bb54244478](images\cfile_3.png)

*Different types of files*

![image-20250719212841299](images\image-16.png)

- **Realtime Conversation**

![image-20250719213320916](images\image-17.png)
