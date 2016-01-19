Code Guidelines for Eezee-It Developers and Contributors
---------------------------------------
The rules below are not guidelines or recommendations, but strict rules. Pull requests generally will not be accepted if they do not adhere to these rules.

Not all existing code follows these rules, but all new code is expected to.

#### Python Language Rules
--------------------------
We follow standard Python code conventions decribed in [PEP-8](https://www.python.org/dev/peps/pep-0008/).
- Maximum column length is 79 characters.
- Use 4 spaces per indentation level.

#### Odoo Coding Rules
-----------------------
* **Naming conventions:**
  ```module_name, ClassName, method_name, ExceptionName, CONSTANT_NAME```
* **Specific Odoo naming conventions:**
  - Model names: 
  
    Yes: 
    ```python
    class SomeModel(models.Model):
      _name = 'some.model'
    ```
    Yes: 
    ```python
    class AnotherNewModel(models.Model):
      _name = 'another.new.model'
    ```
    No: 
    ```python
    class AnotherNewModel(models.Model):
      _name = 'another.new_model'
    ```
  - Relational fields names:
    
    For two models declared as:
    ```python
    class ExampleModel(models.Model):
      _name = 'example.model'
      
    class AnotherModel(models.Model):
      _name = 'another.model'
    ```
    + Many to one:
      Use model's **`_name`**, replacing dots with underscores + **`_id`** suffix
      
      Yes:
      ```python
      example_model_id = fields.Many2one('example.model')
      ```
      Acceptable:
      ```python
      model_id = fields.Many2one('example.model')
      ```
      No:
      ```python
      example_model = fields.Many2one('example.model')
      ```
    + One to many:
      Use model's **`_name`**, replacing dots with underscores + **`_ids`** suffix
      
      Yes:
      ```python
      example_model_ids = fields.One2many('example.model', 'another_model_id')
      ```
      No:
      ```python
      example_models = fields.One2many('example.model', 'another_model_id')
      ```
      Never:
      ```python
      examples = fields.One2many('example.model', 'another_model_id')
      ```
    + Many to many:
    
      Use model's **`_name`**, replacing dots with underscores + **`_ids`** suffix.
      
      *Note:* At field definition, always use prefix **`rel_`** + **`current_model`** + **`related_model`** to define relationship table.
      
      Yes:
      ```python
      example_model_ids = fields.Many2many(
        'example.model', 
        'rel_another_model_example_model', 
        'another_model_id', 'example_model_id')
      ```
      No:
      ```python
      example_models = fields.Many2many(
        'example.model', 
        'rel_another_model_example_model', 
        'another_model_id', 'example_model_id')
      ```
      Never:
      ```python
      examples = fields.Many2many(
        'example.model', 
        'rel_examples', 
        'another_model', 'example_model')
      ```
  
  - Field related methods:
  
    In order to define methods that will be used as arguments in fields declaration:
    1. Always use one leading underscore.
    2. Method's name must refer the kind of argument.
      
    *Examples*:
    ```python
    upper = fields.Char(compute='_compute_upper',
                      inverse='_inverse_upper',
                      search='_search_upper')
    
    @api.depends('name')
    def _compute_upper(self):
      for rec in self:
          rec.upper = rec.name.upper() if rec.name else False
    
    def _inverse_upper(self):
      for rec in self:
          rec.name = rec.upper.lower() if rec.upper else False
    
    def _search_upper(self, operator, value):
      if operator == 'like':
          operator = 'ilike'
      return [('name', operator, value)]
    ```
      
    To define methods used for contraints/onchange decorators:
    1. Constraints: use prefix **`_check`**
        
        ```python
        @api.one
        @api.constrains('available_seats')
        def _check_available_seats(self):
        ...
        ```
    2. On change: use prefix **`_onchange`**
        
        ```python
        @api.onchange('partner_id')
        def _onchange_partner(self):
        ...
        ```
* **Handling exceptions**

  - You must never ignore exceptions.
  - Avoid capturing generic exceptions.
  - Always use a logger to output exceptions messages.
    
  Yes:
  ```python
  try:
    self.validate_voucher()
  except ValidationError as e:
    logger.error(e)
    return False
  ```
  No:
   ```python
  try:
    self.validate_voucher()
  except Exception as e:
    logger.error(e)
  ```
  Never:
  ```python
  try:
    self.validate_voucher()
  except Exception:
    pass
  ```

* **Use TODO Comments**

  Use TODO comments for code that is temporary, a short-term solution, or good-enough but not perfect.

  TODOs should include the string TODO in all caps, followed by a colon:
  ```python
  # TODO: Remove this code after the ResPartnerBank has been checked in.  
  ```