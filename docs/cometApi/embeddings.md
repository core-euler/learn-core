# Embeddings

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/embeddings:
    post:
      summary: Embeddings
      deprecated: false
      description: >-
        ### Embeddings API


        This API endpoint allows you to generate embeddings for text using a
        specific model.


        #### Request Body


        - `model` (string, required): The name of the text embedding model to be
        used.
            
        - `input` (string, required): The input text for which embeddings need
        to be generated.
      tags:
        - 💬 Text Models
      parameters:
        - name: Authorization
          in: header
          description: ''
          required: true
          example: Bearer {{api-key}}
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                model:
                  type: string
                  description: >-
                    The ID of the model you want to use. You can use the List
                    models API
                    :https://platform.openai.com/docs/api-reference/models/list
                    to see all available models, or see our model overview:
                    https://platform. openai.com/docs/models/overview for their
                    descriptions.
                input:
                  type: string
                  description: >-
                    Enter text for embedding, encoded as a string or as an array
                    of tokens. To get embeddings for multiple inputs in a single
                    request, pass an array of strings or an array of tokens.
                    Each input must be no longer than 8192 tokens.
              required:
                - model
                - input
              x-apidog-orders:
                - model
                - input
            example:
              model: text-embedding-3-large
              input: The food was delicious and the waiter...
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  object:
                    type: string
                    description: |
                      The type of the top-level object.
                  data:
                    type: array
                    items:
                      type: object
                      properties:
                        object:
                          type: string
                          description: |
                            The type of the object within the list, 
                        index:
                          type: integer
                          description: >
                            The index of this embedding vector in the input (if
                            the input is bulk) or output list, starting from 0.
                        embedding:
                          type: array
                          items:
                            type: number
                          description: |
                            The actual embedding vector.
                      x-apidog-orders:
                        - object
                        - index
                        - embedding
                    description: >-
                      A list containing embedding vector objects. If the input
                      requests more than one text embedding, there will be more
                      than one object in this list.
                  model:
                    type: string
                    description: >
                      The name of the specific model used to generate the
                      embedding vector.
                  usage:
                    type: object
                    properties:
                      prompt_tokens:
                        type: integer
                        description: >
                          The number of tokens used by the input text (hints)
                          after it has been split.
                      total_tokens:
                        type: integer
                        description: The total number of tokens processed for this request.
                    required:
                      - prompt_tokens
                      - total_tokens
                    x-apidog-orders:
                      - prompt_tokens
                      - total_tokens
                    description: |
                      The token usage statistics for this request.
                required:
                  - object
                  - data
                  - model
                  - usage
                x-apidog-orders:
                  - object
                  - data
                  - model
                  - usage
          headers: {}
          x-apidog-name: Successful Response
      security: []
      x-apidog-folder: 💬 Text Models
      x-apidog-status: released
      x-run-in-apidog: https://app.apidog.com/web/project/810968/apis/api-13851473-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://api.cometapi.com
    description: Prod Env
security: []

```