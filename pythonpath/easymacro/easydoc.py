#!/usr/bin/env python3

import uno
from .easymain import (log,
    BaseObject, LOMain, Paths,
    dict_to_property, create_instance
)
from .easyuno import IOStream
from .easyshape import LOShapes, LOShape


class LOLayoutManager(BaseObject):
    PR = 'private:resource/'

    def __init__(self, obj):
        super().__init__(obj)

    def __getitem__(self, index):
        """ """
        name = index
        if not name.startswith(self.PR):
            name = self.PR + name
        return self.obj.getElement(name)

    @property
    def visible(self):
        """ """
        return self.obj.isVisible()
    @visible.setter
    def visible(self, value):
        self.obj.Visible = value

    @property
    def elements(self):
        """ """
        return [e.ResourceURL[17:] for e in self.obj.Elements]

    def show(self, name):
        if not name.startswith(self.PR):
            name = self.PR + name
        self.obj.showElement(name)
        return

    def hide(self, name):
        if not name.startswith(self.PR):
            name = self.PR + name
        self.obj.hideElement(name)
        return

    # ~ def create(self, name):
        # ~ return self.obj.createElement(name)


class LODocument(BaseObject):

    def __init__(self, obj):
        super().__init__(obj)
        self._cc = obj.getCurrentController()
        self._layout_manager = LOLayoutManager(self._cc.Frame.LayoutManager)
        self._undo = True
        self._cw = self._cc.Frame.ContainerWindow

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def type(self):
        """Get type document"""
        return self._type

    @property
    def title(self):
        """Get title document"""
        return self.obj.getTitle()
    @title.setter
    def title(self, value):
        self.obj.setTitle(value)

    @property
    def uid(self):
        """Get Runtime UID"""
        return self.obj.RuntimeUID

    @property
    def is_saved(self):
        """Get is saved"""
        return self.obj.hasLocation()

    @property
    def is_modified(self):
        """Get is modified"""
        return self.obj.isModified()

    @property
    def is_read_only(self):
        """Get is read only"""
        return self.obj.isReadonly()

    @property
    def path(self):
        """Get path in system files"""
        return Paths.to_system(self.obj.URL)

    @property
    def dir(self):
        """Get directory from path"""
        return Paths(self.path).path

    @property
    def file_name(self):
        """Get only file name"""
        return Paths(self.path).file_name

    @property
    def name(self):
        """Get name without extension"""
        return Paths(self.path).name

    @property
    def visible(self):
        """Get windows visible"""
        w = self.frame.ContainerWindow
        return w.isVisible()
    @visible.setter
    def visible(self, value):
        w = self.frame.ContainerWindow
        w.setVisible(value)

    @property
    def zoom(self):
        """Get current zoom value"""
        return self._cc.ZoomValue
    @zoom.setter
    def zoom(self, value):
        self._cc.ZoomValue = value

    @property
    def status_bar(self):
        """Get status bar"""
        bar = self._cc.getStatusIndicator()
        return bar

    @property
    def selection(self):
        """Get current selecction"""
        sel = self.obj.CurrentSelection
        return sel

    @property
    def frame(self):
        """Get frame document"""
        return self._cc.getFrame()

    @property
    def layout_manager(self):
        """ """
        return self._layout_manager

    def _create_instance(self, name):
        obj = self.obj.createInstance(name)
        return obj

    def save(self, path: str='', args: dict={}) -> bool:
        """Save document

        :param path: Path to save document
        :type path: str
        :param args: Optional: Extra argument for save
        :type args: dict
        :return: True if save correctly, False if not
        :rtype: bool
        """
        if not path:
            self.obj.store()
            return True

        path_save = Paths.to_url(path)
        opt = dict_to_property(args)

        try:
            self.obj.storeAsURL(path_save, opt)
        except Exception as e:
            log.error(e)
            return False

        return True

    def close(self):
        """Close document"""
        self.obj.close(True)
        return

    def to_pdf(self, path: str='', args: dict={}):
        """Export to PDF

        :param path: Path to export document
        :type path: str
        :param args: Optional: Extra argument for export
        :type args: dict
        :return: None if path or stream in memory
        :rtype: bytes or None

        `See PDF Export <https://wiki.documentfoundation.org/Macros/Python_Guide/PDF_export_filter_data>`_
        """
        stream = None
        path_pdf = 'private:stream'

        filter_name = f'{self.type}_pdf_Export'
        filter_data = dict_to_property(args, True)
        filters = {
            'FilterName': filter_name,
            'FilterData': filter_data,
        }
        if path:
            path_pdf = Paths.to_url(path)
        else:
            stream = IOStream.output()
            filters['OutputStream'] = stream

        opt = dict_to_property(filters)
        try:
            self.obj.storeToURL(path_pdf, opt)
        except Exception as e:
            error(e)

        if not stream is None:
            stream = stream.buffer

        return stream

    def export(self, path: str='', filter_name: str='', args: dict={}):
        """Export to others formats

        :param path: Path to export document
        :type path: str
        :param filter_name: Filter name to export
        :type filter_name: str
        :param args: Optional: Extra argument for export
        :type args: dict
        :return: None if path or stream in memory
        :rtype: bytes or None

        https://api.libreoffice.org/docs/idl/ref/servicecom_1_1sun_1_1star_1_1document_1_1MediaDescriptor.html
        """
        FILTERS = {
            'xlsx': 'Calc MS Excel 2007 XML',
            'xls': 'MS Excel 97',
            'docx': 'MS Word 2007 XML',
            'doc': 'MS Word 97',
            'rtf': 'Rich Text Format',
        }

        stream = None
        path_target = 'private:stream'
        if filter_name == 'svg':
            filter_name = f'{self.type}_svg_Export'
        else:
            filter_name = FILTERS.get(filter_name, filter_name)

        filter_data = dict_to_property(args, True)
        filters = {
            'FilterName': filter_name,
            'FilterData': filter_data,
        }
        if path:
            path_target = Paths.to_url(path)
        else:
            stream = IOStream.output()
            filters['OutputStream'] = stream

        opt = dict_to_property(filters)
        try:
            self.obj.storeToURL(path_target, opt)
        except Exception as e:
            log.error(e)

        if not stream is None:
            stream = stream.buffer

        return stream

    def set_focus(self):
        """Send focus to windows"""
        w = self.frame.ComponentWindow
        w.setFocus()
        return

    def copy(self):
        """Copy current selection"""
        LOMain.dispatch(self.frame, 'Copy')
        return

    def cut(self):
        """Cut current selection"""
        LOMain.dispatch(self.frame, 'Cut')
        return

    def paste(self):
        """Paste current content in clipboard"""
        sc = create_instance('com.sun.star.datatransfer.clipboard.SystemClipboard')
        transferable = sc.getContents()
        self._cc.insertTransferable(transferable)
        return

    def paste_special(self):
        """Insert contents, show dialog box Paste Special"""
        LOMain.dispatch(self.frame, 'InsertContents')
        return

    def paste_values(self):
        """Paste only values"""
        args = {
            'Flags': 'SVD',
            # ~ 'FormulaCommand': 0,
            # ~ 'SkipEmptyCells': False,
            # ~ 'Transpose': False,
            # ~ 'AsLink': False,
            # ~ 'MoveMode': 4,
        }
        LOMain.dispatch(self.frame, 'InsertContents', args)
        return

    def clear_undo(self):
        """Clear history undo"""
        self.obj.getUndoManager().clear()
        return

    def replace_ext(self, new_ext):
        return Paths.with_suffix(self.path, new_ext)

    def deselect(self):
        LOMain.dispatch(self.frame, 'Deselect')
        return

    #  def clear_format(self):
        #  """Clear Direct Formatting"""
        #  LOMain.dispatch(self.frame, 'SetDefault')
        #  return


class LODrawImpress(LODocument):
    from .easydrawpage import LODrawPage

    def __init__(self, obj):
        super().__init__(obj)

    def __getitem__(self, index):
        if isinstance(index, int):
            page = self.obj.DrawPages[index]
        else:
            page = self.obj.DrawPages.getByName(index)
        return self.LODrawPage(page)

    @property
    def selection(self):
        """Get current selecction"""
        sel = self.obj.CurrentSelection
        if sel.Count == 1:
            sel = LOShape(sel[0])
        else:
            sel = LOShapes(sel)
        return sel

    @property
    def current_page(self):
        return self.LODrawPage(self._cc.CurrentPage)
    @property
    def active(self):
        return self.current_page
