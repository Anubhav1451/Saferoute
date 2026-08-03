## Failed Command 1: TestResolverIntegration.test_resolve_unknown_highway_returns_unresolved

**Command**: python -m pytest -m integration -v 2>&1

**Stdout**:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- D:\Python312\python.exe
cachedir: .pytest_cache
rootdir: D:\saferoute-ai\backend
plugins: anyio-4.14.2
collecting ... collected 163 items / 157 deselected / 6 selected

tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_unknown_highway_returns_unresolved FAILED [ 16%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_returns_dict FAILED [ 33%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_populates_metadata FAILED [ 50%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve PASSED [ 66%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve_empty PASSED [ 83%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve_error_handling PASSED [100%]
```

**Stderr**:

```
___ TestResolverIntegration.test_resolve_unknown_highway_returns_unresolved ___

self = <sqlalchemy.engine.base.Connection object at 0x0000029D7C0A3230>
dialect = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D3FB3AB10>
statement = <sqlalchemy.dialects.sqlite.base.SQLiteCompiler object at 0x0000029D3F072AE0>
parameters = [('',)]

    def _exec_single_context(
        self,
        dialect: Dialect,
        context: ExecutionContext,
        statement: Union[str, Compiled],
        parameters: Optional[_AnyMultiExecuteParams],
    ) -> CursorResult[Any]:
        """continue the _execute_context() method for a single DBAPI
        cursor.execute() or cursor.executemany() call.
    
        """
        if dialect.bind_typing is BindTyping.SETINPUTSIZES:
            generic_setinputsizes = context._prepare_set_input_sizes()
    
            if generic_setinputsizes:
                try:
                    dialect.do_set_input_sizes(
                        context.cursor, generic_setinputsizes, context
                    )
                except BaseException as e:
                    self._handle_dbapi_exception(
                        e, str(statement), parameters, None, context
                    )
    
        cursor, str_statement, parameters = (
            context.cursor,
            context.statement,
            context.parameters,
        )
    
        effective_parameters: Optional[_AnyExecuteParams]
    
        if not context.executemany:
            effective_parameters = parameters[0]
        else:
            effective_parameters = parameters
    
        if self._has_events or self.engine._has_events:
            for fn in self.dispatch.before_cursor_execute:
                str_statement, effective_parameters = fn(
                    self,
                    cursor,
                    str_statement,
                    effective_parameters,
                    context,
                    context.executemany,
                )
    
        if self._echo:
            self._log_info(str_statement)
    
            stats = context._get_cache_stats()
    
            if not self.engine.hide_parameters:
                self._log_info(
                    "[%s] %r",
                    stats,
                    sql_util._repr_params(
                        effective_parameters,
                        batches=10,
                        ismulti=context.executemany,
                    ),
                )
            else:
                self._log_info(
                    "[%s] [SQL parameters hidden due to hide_parameters=True]",
                    stats,
                )
    
        evt_handled: bool = False
        try:
            if context.execute_style is ExecuteStyle.EXECUTEMANY:
                effective_parameters = cast(
                    "_CoreMultiExecuteParams", effective_parameters
                )
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_executemany:
                        if fn(
                            cursor,
                            str_statement,
                            effective_parameters,
                            context,
                        ):
                            evt_handled = True
                            break
                if not evt_handled:
                    self.dialect.do_executemany(
                        cursor,
                        str_statement,
                        effective_parameters,
                        context,
                    )
            elif not effective_parameters and context.no_parameters:
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_execute_no_params:
                        if fn(cursor, str_statement, context):
                            evt_handled = True
                            break
                if not evt_handled:
                    self.dialect.do_execute_no_params(
                        cursor, str_statement, context
                    )
            else:
                effective_parameters = cast(
                    "_CoreSingleExecuteParams", effective_parameters
                )
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_execute:
                        if fn(
                            cursor,
                            str_statement,
                            effective_parameters,
                            context,
                        ):
                            evt_handled = True
                            break
                if not evt_handled:
>                   self.dialect.do_execute(
                        cursor, str_statement, effective_parameters, context
                    )

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1969: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
cursor = <sqlite3.Cursor object at 0x0000029D417F62C0>
statement = 'SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway \nFROM osm_ways \nWHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?'
parameters = ('',)
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D3FB3AB10>

    def do_execute(self, cursor, statement, parameters, context=None):
>       cursor.execute(statement, parameters)
E       sqlite3.OperationalError: no such table: osm_ways

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\default.py:952: OperationalError

The above exception was the direct cause of the following exception:

self = <test_chainage_resolver.TestResolverIntegration object at 0x0000029D413A3980>

    def test_resolve_unknown_highway_returns_unresolved(self):
        """Resolving a highway that doesn't exist should return unresolved."""
>       result = self.resolver.resolve("ZZ 999", 100.0)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\test_chainage_resolver.py:372: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
scripts\data_ingestion\chainage_resolver.py:731: in resolve
    result = self._try_osm_way_interpolation(normalized, chainage_km, direction)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
scripts\data_ingestion\chainage_resolver.py:326: in _try_osm_way_interpolation
    self.build_ref_index()
scripts\data_ingestion\chainage_resolver.py:270: in build_ref_index
    ).all()
      ^^^^^
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\query.py:2711: in all
    return self._iter().all()  # type: ignore
           ^^^^^^^^^^^^
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\session.py:2373: in execute
    return self._execute_internal(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\session.py:2271: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
cursor = <sqlite3.Cursor object at 0x0000029D417F62C0>
statement = 'SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway \nFROM osm_ways \nWHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?'
parameters = ('',)
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D3FB3AB10>

    def do_execute(self, cursor, statement, parameters, context=None):
>       cursor.execute(statement, parameters)
E       sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: osm_ways
E       [SQL: SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway 
E       FROM osm_ways 
E       WHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?]
E       [parameters: ('',)]
E       (Background on this error at: https://sqlalche.me/e/20/e3q8)

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\default.py:952: OperationalError
```

**Root cause**: The table 'osm_ways' is missing in the database. This is likely because the test is running in a different context or the database has not been populated with the required OSM data for the integration tests.

**Exact file**: scripts\data_ingestion\chainage_resolver.py
**Exact line**: 731

--

## Failed Command 2: TestResolverIntegration.test_resolve_returns_dict

**Command**: python -m pytest -m integration -v 2>&1

**Stdout**:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- D:\Python312\python.exe
cachedir: .pytest_cache
rootdir: D:\saferoute-ai\backend
plugins: anyio-4.14.2
collecting ... collected 163 items / 157 deselected / 6 selected

tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_unknown_highway_returns_unresolved FAILED [ 16%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_returns_dict FAILED [ 33%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_populates_metadata FAILED [ 50%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve PASSED [ 66%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve_empty PASSED [ 83%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve_error_handling PASSED [100%]
```

**Stderr**:

```
______________ TestResolverIntegration.test_resolve_returns_dict ______________

self = <sqlalchemy.engine.base.Connection object at 0x0000029D417DB9B0>
dialect = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D418947A0>
statement = <sqlalchemy.dialects.sqlite.base.SQLiteCompiler object at 0x0000029D3F072AE0>
parameters = [('',)]

    def _exec_single_context(
        self,
        dialect: Dialect,
        context: ExecutionContext,
        statement: Union[str, Compiled],
        parameters: Optional[_AnyMultiExecuteParams],
    ) -> CursorResult[Any]:
        """continue the _execute_context() method for a single DBAPI
        cursor.execute() or cursor.executemany() call.
    
        """
        if dialect.bind_typing is BindTyping.SETINPUTSIZES:
            generic_setinputsizes = context._prepare_set_input_sizes()
    
            if generic_setinputsizes:
                try:
                    dialect.do_set_input_sizes(
                        context.cursor, generic_setinputsizes, context
                    )
                except BaseException as e:
                    self._handle_dbapi_exception(
                        e, str(statement), parameters, None, context
                    )
    
        cursor, str_statement, parameters = (
            context.cursor,
            context.statement,
            context.parameters,
        )
    
        effective_parameters: Optional[_AnyExecuteParams]
    
        if not context.executemany:
            effective_parameters = parameters[0]
        else:
            effective_parameters = parameters
    
        if self._has_events or self.engine._has_events:
            for fn in self.dispatch.before_cursor_execute:
                str_statement, effective_parameters = fn(
                    self,
                    cursor,
                    str_statement,
                    effective_parameters,
                    context,
                    context.executemany,
                )
    
        if self._echo:
            self._log_info(str_statement)
    
            stats = context._get_cache_stats()
    
            if not self.engine.hide_parameters:
                self._log_info(
                    "[%s] %r",
                    stats,
                    sql_util._repr_params(
                        effective_parameters,
                        batches=10,
                        ismulti=context.executemany,
                    ),
                )
            else:
                self._log_info(
                    "[%s] [SQL parameters hidden due to hide_parameters=True]",
                    stats,
                )
    
        evt_handled: bool = False
        try:
            if context.execute_style is ExecuteStyle.EXECUTEMANY:
                effective_parameters = cast(
                    "_CoreMultiExecuteParams", effective_parameters
                )
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_executemany:
                        if fn(
                            cursor,
                            str_statement,
                            effective_parameters,
                            context,
                        ):
                            evt_handled = True
                            break
                if not evt_handled:
                    self.dialect.do_executemany(
                        cursor,
                        str_statement,
                        effective_parameters,
                        context,
                    )
            elif not effective_parameters and context.no_parameters:
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_execute_no_params:
                        if fn(cursor, str_statement, context):
                            evt_handled = True
                            break
                if not evt_handled:
                    self.dialect.do_execute_no_params(
                        cursor, str_statement, context
                    )
            else:
                effective_parameters = cast(
                    "_CoreSingleExecuteParams", effective_parameters
                )
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_execute:
                        if fn(
                            cursor,
                            str_statement,
                            effective_parameters,
                            context,
                        ):
                            evt_handled = True
                            break
                if not evt_handled:
>                   self.dialect.do_execute(
                        cursor, str_statement, effective_parameters, context
                    )

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1969: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
cursor = <sqlite3.Cursor object at 0x0000029D42CBCA40>
statement = 'SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway \nFROM osm_ways \nWHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?'
parameters = ('',)
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D418947A0>

    def do_execute(self, cursor, statement, parameters, context=None):
>       cursor.execute(statement, parameters)
E       sqlite3.OperationalError: no such table: osm_ways

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\default.py:952: OperationalError

The above exception was the direct cause of the following exception:

self = <test_chainage_resolver.TestResolverIntegration object at 0x0000029D413A3C80>

    def test_resolve_returns_dict(self):
        """to_dict should produce a JSON-serializable dict."""
>       result = self.resolver.resolve("NH 44", 100.0)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\test_chainage_resolver.py:380: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
scripts\data_ingestion\chainage_resolver.py:731: in resolve
    result = self._try_osm_way_interpolation(normalized, chainage_km, direction)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
scripts\data_ingestion\chainage_resolver.py:326: in _try_osm_way_interpolation
    self.build_ref_index()
scripts\data_ingestion\chainage_resolver.py:270: in build_ref_index
    ).all()
      ^^^^^
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\query.py:2711: in all
    return self._iter().all()  # type: ignore
           ^^^^^^^^^^^^
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\session.py:2373: in execute
    return self._execute_internal(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\session.py:2271: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
cursor = <sqlite3.Cursor object at 0x0000029D42CBCA40>
statement = 'SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway \nFROM osm_ways \nWHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?'
parameters = ('',)
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D418947A0>

    def do_execute(self, cursor, statement, parameters, context=None):
>       cursor.execute(statement, parameters)
E       sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: osm_ways
E       [SQL: SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway 
E       FROM osm_ways 
E       WHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?]
E       [parameters: ('',)]
E       (Background on this error at: https://sqlalche.me/e/20/e3q8)

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\default.py:952: OperationalError
```

**Root cause**: The table 'osm_ways' is missing in the database. This is likely because the test is running in a different context or the database has not been populated with the required OSM data for the integration tests.

**Exact file**: scripts\data_ingestion\chainage_resolver.py
**Exact line**: 731

--

## Failed Command 3: TestResolverIntegration.test_resolve_populates_metadata

**Command**: python -m pytest -m integration -v 2>&1

**Stdout**:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- D:\Python312\python.exe
cachedir: .pytest_cache
rootdir: D:\saferoute-ai\backend
plugins: anyio-4.14.2
collecting ... collected 163 items / 157 deselected / 6 selected

tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_unknown_highway_returns_unresolved FAILED [ 16%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_returns_dict FAILED [ 33%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_populates_metadata FAILED [ 50%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve PASSED [ 66%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve_empty PASSED [ 83%]
tests/test_chainage_resolver.py::TestResolverIntegration::test_batch_resolve_error_handling PASSED [100%]
```

**Stderr**:

```
___________ TestResolverIntegration.test_resolve_populates_metadata ___________

self = <sqlalchemy.engine.base.Connection object at 0x0000029D41896F90>
dialect = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D418976E0>
statement = <sqlalchemy.dialects.sqlite.base.SQLiteCompiler object at 0x0000029D3F072AE0>
parameters = [('',)]

    def _exec_single_context(
        self,
        dialect: Dialect,
        context: ExecutionContext,
        statement: Union[str, Compiled],
        parameters: Optional[_AnyMultiExecuteParams],
    ) -> CursorResult[Any]:
        """continue the _execute_context() method for a single DBAPI
        cursor.execute() or cursor.executemany() call.
    
        """
        if dialect.bind_typing is BindTyping.SETINPUTSIZES:
            generic_setinputsizes = context._prepare_set_input_sizes()
    
            if generic_setinputsizes:
                try:
                    dialect.do_set_input_sizes(
                        context.cursor, generic_setinputsizes, context
                    )
                except BaseException as e:
                    self._handle_dbapi_exception(
                        e, str(statement), parameters, None, context
                    )
    
        cursor, str_statement, parameters = (
            context.cursor,
            context.statement,
            context.parameters,
        )
    
        effective_parameters: Optional[_AnyExecuteParams]
    
        if not context.executemany:
            effective_parameters = parameters[0]
        else:
            effective_parameters = parameters
    
        if self._has_events or self.engine._has_events:
            for fn in self.dispatch.before_cursor_execute:
                str_statement, effective_parameters = fn(
                    self,
                    cursor,
                    str_statement,
                    effective_parameters,
                    context,
                    context.executemany,
                )
    
        if self._echo:
            self._log_info(str_statement)
    
            stats = context._get_cache_stats()
    
            if not self.engine.hide_parameters:
                self._log_info(
                    "[%s] %r",
                    stats,
                    sql_util._repr_params(
                        effective_parameters,
                        batches=10,
                        ismulti=context.executemany,
                    ),
                )
            else:
                self._log_info(
                    "[%s] [SQL parameters hidden due to hide_parameters=True]",
                    stats,
                )
    
        evt_handled: bool = False
        try:
            if context.execute_style is ExecuteStyle.EXECUTEMANY:
                effective_parameters = cast(
                    "_CoreMultiExecuteParams", effective_parameters
                )
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_executemany:
                        if fn(
                            cursor,
                            str_statement,
                            effective_parameters,
                            context,
                        ):
                            evt_handled = True
                            break
                if not evt_handled:
                    self.dialect.do_executemany(
                        cursor,
                        str_statement,
                        effective_parameters,
                        context,
                    )
            elif not effective_parameters and context.no_parameters:
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_execute_no_params:
                        if fn(cursor, str_statement, context):
                            evt_handled = True
                            break
                if not evt_handled:
                    self.dialect.do_execute_no_params(
                        cursor, str_statement, context
                    )
            else:
                effective_parameters = cast(
                    "_CoreSingleExecuteParams", effective_parameters
                )
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_execute:
                        if fn(
                            cursor,
                            str_statement,
                            effective_parameters,
                            context,
                        ):
                            evt_handled = True
                            break
                if not evt_handled:
>                   self.dialect.do_execute(
                        cursor, str_statement, effective_parameters, context
                    )

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1969: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
cursor = <sqlite3.Cursor object at 0x0000029D4276F1C0>
statement = 'SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway \nFROM osm_ways \nWHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?'
parameters = ('',)
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D418976E0>

    def do_execute(self, cursor, statement, parameters, context=None):
>       cursor.execute(statement, parameters)
E       sqlite3.OperationalError: no such table: osm_ways

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\default.py:952: OperationalError

The above exception was the direct cause of the following exception:

self = <test_chainage_resolver.TestResolverIntegration object at 0x0000029D413A3F80>

    def test_resolve_populates_metadata(self):
        """Resolution metadata should always be populated."""
>       result = self.resolver.resolve("NH 44", 100.0)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\test_chainage_resolver.py:391: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
scripts\data_ingestion\chainage_resolver.py:731: in resolve
    result = self._try_osm_way_interpolation(normalized, chainage_km, direction)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
scripts\data_ingestion\chainage_resolver.py:326: in _try_osm_way_interpolation
    self.build_ref_index()
scripts\data_ingestion\chainage_resolver.py:270: in build_ref_index
    ).all()
      ^^^^^
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\query.py:2711: in all
    return self._iter().all()  # type: ignore
           ^^^^^^^^^^^^
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\query.py:2864: in _iter
    result: Union[ScalarResult[_T], Result[_T]] = self.session.execute(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\session.py:2373: in execute
    return self._execute_internal(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\session.py:2271: in _execute_internal
    result: Result[Any] = compile_state_cls.orm_execute_statement(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\orm\context.py:306: in orm_execute_statement
    result = conn.execute(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1421: in execute
    return meth(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\sql\elements.py:526: in _execute_on_connection
    return connection._execute_clauseelement(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1643: in _execute_clauseelement
    ret = self._execute_context(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1848: in _execute_context
    return self._exec_single_context(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1988: in _exec_single_context
    self._handle_dbapi_exception(
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:2365: in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\base.py:1969: in _exec_single_context
    self.dialect.do_execute(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <sqlalchemy.dialects.sqlite.pysqlite.SQLiteDialect_pysqlite object at 0x0000029D7E817770>
cursor = <sqlite3.Cursor object at 0x0000029D4276F1C0>
statement = 'SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway \nFROM osm_ways \nWHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?'
parameters = ('',)
context = <sqlalchemy.dialects.sqlite.base.SQLiteExecutionContext object at 0x0000029D418976E0>

    def do_execute(self, cursor, statement, parameters, context=None):
>       cursor.execute(statement, parameters)
E       sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: osm_ways
E       [SQL: SELECT osm_ways.id AS osm_ways_id, osm_ways.ref AS osm_ways_ref, osm_ways.highway AS osm_ways_highway 
E       FROM osm_ways 
E       WHERE osm_ways.ref IS NOT NULL AND osm_ways.ref != ?]
E       [parameters: ('',)]
E       (Background on this error at: https://sqlalche.me/e/20/e3q8)

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\sqlalchemy\engine\default.py:952: OperationalError
============================== warnings summary ===============================
app\db\models.py:7
  D:\saferoute-ai\backend\app\db\models.py:7: MovedIn20Warning: The ``declarative_base()`` function is now available as sqlalchemy.orm.declarative_base(). (deprecated since: 2.0) (Background on SQLAlchemy 2.0 at: https://sqlalche.me/e/b8d9)
    Base = declarative_base()

app\core\config.py:22
  D:\saferoute-ai\backend\app\core\config.py:22: PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'env'). Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")

C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\fastapi\testclient.py:1
  C:\Users\anubh\AppData\Roaming\Python\Python312\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

app\api\responses.py:6
  D:\saferoute-ai\backend\app\api\responses.py:6: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class APIResponse(BaseModel):

tests\test_chainage_resolver.py:354
  D:\saferoute-ai\backend\tests\test_chainage_resolver.py:354: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_unknown_highway_returns_unresolved
FAILED tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_returns_dict
FAILED tests/test_chainage_resolver.py::TestResolverIntegration::test_resolve_populates_metadata
=========== 3 failed, 3 passed, 157 deselected, 5 warnings in 3.73s ===========
```

**Root cause**: The table 'osm_ways' is missing in the database. This is likely because the test is running in a different context or the database has not been populated with the required OSM data for the integration tests.

**Exact file**: scripts\data_ingestion\chainage_resolver.py
**Exact line**: 731

--

