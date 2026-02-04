from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtCore import Qt
from qfluentwidgets import TableWidget

class DraggableTableWidget(TableWidget):
    """
    TableWidget that supports dragging rows to other DraggableTableWidgets.
    Calls ViewModel directly on drop.
    """
    def __init__(self, vm, list_type, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.list_type = list_type # 'required' or 'desired'
        
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)

    def startDrag(self, supportedActions):
        # Override to ensure we don't let QAbstractItemView handle the 'move' deletion
        # We handle data updates via ViewModel.
        super().startDrag(Qt.CopyAction)

    def dragEnterEvent(self, event):
        if isinstance(event.source(), DraggableTableWidget):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if isinstance(event.source(), DraggableTableWidget):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        source = event.source()
        if not isinstance(source, DraggableTableWidget):
            return 
            
        if source == self:
            # Reordering
            source_row = source.currentRow()
            
            # Determine target row using dropPos
            drop_pos = event.pos()
            target_item = self.itemAt(drop_pos)
            
            if target_item:
                target_row = self.row(target_item)
            else:
                 # Dropped in empty space? Append to end or determine if 'top' or 'bottom'
                 # Roughly, if Y is large, end.
                 target_row = self.rowCount()
            
            if self.vm.reorder_course(self.list_type, source_row, target_row):
                 pass
            
            # IMPORTANT: Tell source valid drop happened, but use CopyAction 
            # so source view doesn't try to delete the row (VM does it).
            event.setDropAction(Qt.CopyAction) 
            event.accept()
            return

        source_row = source.currentRow()
        if source_row < 0:
            return
            
        # Execute Move via ViewModel
        if self.vm.move_course(source.list_type, self.list_type, source_row):
             pass
        
        # Prevent source from automatically removing the row (since ViewModel handles it)
        event.setDropAction(Qt.CopyAction)
        event.accept()
